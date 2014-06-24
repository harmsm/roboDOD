#!/usr/bin/env python

from robotDevices import TwoMotorDriveSteer
import time

def cleanUp(m):
    """
    """

    m.sendData("stop")
    m.sendData("coast")
    m.sendData("center")

try:

    m = TwoMotorDriveSteer(13,15,7,11)

    m.sendData("coast")
    m.sendData("center")

    m.sendData("forward")
    time.sleep(2)
    m.sendData("reverse")
    time.sleep(2)
    m.sendData("stop")

    for i in range(3):
        m.sendData("right"); time.sleep(0.3)
        m.sendData("left"); time.sleep(0.3)

    for i in range(2):
        m.sendData("right")
        m.sendData("forward")
        time.sleep(3)

        m.sendData("stop")
        m.sendData("left")
        m.sendData("reverse")
        time.sleep(3)

    m.sendData("right")
    m.sendData("forward")
    time.sleep(3)
    
    m.sendData("coast")
    
except:
    cleanUp(m)

cleanUp(m)
