__description__ = \
"""
This is a fake gpio interface so that this software can be run and tested
without actually being on a raspberry pi.
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-20"

def output(*args,**kwargs):
    print("WARNING! Using simulated GPIO interface.")

def input(*args,**kwargs):
    print("WARNING! Using simulated GPIO interface.")
    return 0

def PWM(*args,**kwargs):
    print("WARNING! Using simulated GPIO interface.")

def cleanup(*args,**kwargs):
    print("WARNING! Using simulated GPIO interface.")

def setup(*args,**kwargs):
    print("WARNING! Using simulated GPIO interface.")

def setmode(*args,**kwargs):
    print("WARNING! Using simulated GPIO interface.")

def setwarnings(*args,**kwargs):
    print("WARNING! Using simulated GPIO interface.")

IN = 0
OUT = 1
BOARD = 0
