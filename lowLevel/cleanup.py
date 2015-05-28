#!/usr/bin/env python3
__description__ = \
"""
Simple script to make sure all gpio pins are in the off state on boot.
"""
__author__ = "Michael J. Harms"
__usage__ = "run via rc.local"
__date__ = "2015-03-10"

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
for i in range(1,27): 

    try:
        GPIO.setup(i, GPIO.OUT)
        GPIO.output(i,False)
    except ValueError:
        continue
    
GPIO.cleanup()
