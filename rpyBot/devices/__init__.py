__description__ = \
"""
The class RobotDevice (and its childern), are used to provide the hardware-
specific functions required for each device.  Each class has public methods:

connect_manager: put device under exclusive control of a DeviceManager instance
disconnect_manager: drop current controlling DeviceManager instance
get: get any messages since last polled, clearing messages
put: send a command to the device (via private methods in _control_dict)
start: start the device
stop: safely shutdown the hardware

All other methods should private and controlled via the put() method, which 
takes a RobotMessage instance.  The "message" attribute should have a string
key which maps to a callback specified in the _control_dict of the device.

    "key" OR
    ["key",{kwarg1:value1,kwarg2:value2...}"]

When writing methods, all functions should access self._messages via the 
self._append_message and self._get_messages methods, as these use a re-enterant
thread lock to stay thread-safe.  This is critical because the tornado server
and device manager are on different threads but can both post messages.
""" 
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

__all__ = ["arduino","gpio","web"]

from .robot_device import RobotDevice
from . import gpio, arduino, web

