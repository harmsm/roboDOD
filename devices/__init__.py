"""
These classes, built on the base-class RobotDevice, are used to provide the
hardware-specific functions required for each device.  Each class has six 
public methods:

connectManager: put device under exclusive control of a DeviceManager instance
disconnectManager: drop current controlling DeviceManager instance
get: get any messages since last polled, clearing messages
put: send a command to the device (via private methods in _control_dict)
get_now: return data from device directly, skipping asynchrony
shutdown: safely shutdown the hardware

All other methods should private and controlled via the put() method. put takes
a command of the form:

    "key" OR
    ["key",{kwarg1:value1,kwarg2:value2...}"]

When writing methods, all functions should access self._messages via the 
self._append_message and self._get_messages methods, as these use a re-enterant
thread lock to stay thread-safe.  This is critical because the tornado server
and device manager are on different threads but can both post messages.
""" 
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

__all__ = ["drivetrain","led","rangefinder"] 


from .main import RobotDevice, DummyDevice
