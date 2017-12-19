import struct
import sys

class serialPort(object):
    def __init__(self, serial):
        self.port = serial

    def read(self, size):
        char = self.port.read(size)
        if sys.version_info >= (3,0,0):
            char = str(char, 'UTF-8')
        return char

    def write(self, char):
        if sys.version_info >= (3,0,0):
            char = bytes(char, 'UTF-8')
        self.port.write(char)

    def readByte(self):
        res = self.port.read(1)
        if len(res) > 0:
            val = struct.unpack('>B', res)
            return val[0]
        return None


