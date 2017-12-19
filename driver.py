import threading
import traceback
import sys

import time

LASER_ON = 'BM\n'
LASER_OFF = 'QT\n'
RESET = 'RS\n'
VERSION_INFO = 'VV\n'
SENSOR_STATE = 'II\n'
SENSOR_SPECS = 'PP\n'
SET_SCIP2 = 'SCIP2.0\n'

VERSION_INFO_LINES = 6
SENSOR_STATE_LINES = 8
SENSOR_SPECS_LINES = 9

CHARS_PER_VALUE = 3.0
CHARS_PER_LINE = 66.0
CHARS_PER_BLOCK = 64.0

START_DEG = 119.885
STEP_DEG = 0.35208516886930985
START_STEP = 44
STOP_STEP = 725

MD_COMMAND_REPLY_LEN = 20

class Driver(object):

    def __init__ (self, serialPort):
        self.serialPort = serialPort
        self.portLock = threading.RLock()
        self.timestamp, self.angles, self.distances = 0, [], []
        self.scanLock = threading.RLock()

    def sendCommand(self, command):
        self.portLock.acquire()
        try:
            self.serialPort.write(command)
            result = self.serialPort.read(len(command))
            assert result == command
        finally:
            self.portLock.release()
        return result

    def shortCommand(self, command, checkResponse=True):
        result = ''
        self.portLock.acquire()
        try:
            try:
                result += self.sendCommand(command)
                result += self.serialPort.read(5)

                if checkResponse:
                    assert result[-5:-2] == '00P'
                assert result[-2:] == '\n\n'

                return result
            
            except BaseException as e:
                sys.stderr.write('RESULT: "%s"' % result)
                traceback.print_exc()

        finally:
            self.portLock.release()


    def longCommand(self, command, lines, checkResponse=True):
        result = ''
        self.portLock.acquire()
        try:
            try:
                result += self.sendCommand(command)
                result += self.serialPort.read(4)

                if checkResponse:
                    assert result[-4:-1] == '00P'
                assert result[-1:] == '\n'

                line = 0
                while line < lines:
                    char = self.serialPort.readByte()
                    if not char is None:
                        char = chr(char)
                        result += char
                        if char == '\n':
                            line += 1
                    else:
                        line += 1

                assert result[-2:] == '\n\n'

                return result
            except BaseException as e:
                sys.stderr.write('RESULT: "%s"' % result)
                traceback.print_exc()
        finally:
            self.portLock.release()


    def laserOn(self):
        return self.shortCommand(LASER_ON, checkResponse=True)

    def laserOff(self):
        return self.shortCommand(LASER_OFF)

    def reset(self):
        return self.shortCommand(RESET)

    def setScip2(self):
        "for URG-04LX"
        return self.shortCommand(SET_SCIP2, checkResponse=False)

    def setMotorSpeed(self, motorSpeed=99):
        return self.shortCommand('CR' + '%02d' % motorSpeed + '\n', checkResponse=False)

    def setHighSensitive(self, enable=True):
        return self.shortCommand('HS' + ('1\n' if enable else '0\n'), checkResponse=False)

    def getVersionInfo(self):
        return self.longCommand(VERSION_INFO, VERSION_INFO_LINES)

    def getSensorState(self):
        return self.longCommand(SENSOR_STATE, SENSOR_STATE_LINES)

    def getSensorSpecs(self):
        return self.longCommand(SENSOR_SPECS, SENSOR_SPECS_LINES)

    def getAndParseScan(self, clusterCount, startStep, stopStep):
        distances = {}
        result = ''

        count = ((stopStep - startStep) * CHARS_PER_VALUE * CHARS_PER_LINE)
        count /= (CHARS_PER_BLOCK * clusterCount)

        count += 1.0 + 4.0
        count = int(count)

        self.portLock.acquire()
        try:
            result += self.serialPort.read(count)
        finally:
            self.portLock.release()

        assert result[-2:] == '\n\n'

        result = result.split('\n')
        result = [line[:-1] for line in result]
        result = ''.join(result)

        i = 0
        start = (-START_DEG + STEP_DEG * clusterCount * (startStep - START_STEP))
        for chunk in self.chunks(result, 3):
            distances[- ((STEP_DEG * clusterCount * i) + start)] = self.decode(chunk)
            i += 1

        return distances


    def singleScan(self, startStep=START_STEP, stopStep=STOP_STEP, clusterCount=1):
        self.portLock.acquire()
        try:
            command = 'GD%04d%04d%02d\n' % (startStep, stopStep, clusterCount)
            self.serialPort.write(command)

            result = self.serialPort.read(len(command))
            assert result == command

            result += self.serialPort.read(4)
            assert result[-4:-1] == '00P'
            assert result[-1] == '\n'

            result = self.serialPort.read(6)
            assert result[-1] == '\n'

            scan = self.getAndParseScan(clusterCount, startStep, stopStep)
            return scan

        except BaseException as e:
            traceback.print_exc()

        finally:
            self.portLock.release()


    def setScan(self, scan):
        if scan is not None:
            timestamp = int(time.time() * 1000.0)
            angles, distances = self.parseScan(scan)

            self.scanLock.acquire()
            try:
                self.angles, self.distances, self.timestamp = angles, distances, timestamp
            finally:
                self.scanLock.release()

    def getScan(self):
        scan = self.singleScan()
        self.setScan(scan)

        self.scanLock.acquire()
        try:
            return self.angles, self.distances, self.timestamp
        finally:
            self.scanLock.release()
    
    def parseScan(self, scan):
        angles = sorted(scan.keys())
        distances = list(map(scan.get, angles))
        return angles, distances


    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def decode(self, val):
        binaryStr = '0b'
        for char in val:
            val = ord(char) - 0x30
            binaryStr += '%06d' % int(bin(val)[2:])
        return int(binaryStr, 2)




































































































