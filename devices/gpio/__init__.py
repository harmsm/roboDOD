__description__ = \
"""
Connector that allows messaging with arduino boards via a USB connection.  It 
uses the CmdMessenger (https://github.com/thijse/Arduino-CmdMessenger) to 
manage the information passed over serial. 
"""
__author__ = "Michael J. Harms"
__date__ = "2016-05-20"

__all__ = ["led",
           "drivetrain",
           "rangefinder"]

from . import gpio
