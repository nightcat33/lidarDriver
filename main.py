import serial

from driver import *
from serialPort import *

import numpy as np
import matplotlib.pyplot as plt

import signal

from signal import SIGINT, SIGTERM
from pysigset import suspended_signals

import time

uartPort = '/dev/tty.usbmodem14611'
uartSpeed = 19200

laserSerial = serial.Serial(port=uartPort, baudrate=uartSpeed, timeout=0.5)
port = serialPort(laserSerial)
laser = Driver(port)

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    laser.laserOff()

    time.sleep(5)
    sys.exit(0)

if __name__ == '__main__':


    signal.signal(signal.SIGINT, signal_handler)

    print(laser.getSensorState())
    laser.laserOn()

    plt.ion()

    while True:
        with suspended_signals(SIGINT, SIGTERM):
            angles, distances, _ = laser.getScan()
            for i in range(len(angles)):
                if angles[i] < 0:
                    angles[i] += 360 
                angles[i] = angles[i] * np.pi / 180
            plt.gcf().clear()
            plt.polar(angles, distances, color='r')
            plt.pause(0.0001)





