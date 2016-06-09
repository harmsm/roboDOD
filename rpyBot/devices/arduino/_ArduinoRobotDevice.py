__description__ = \
"""
Base class for allowing communication between the raspberry pi robot controller
and an arduino slave.
"""
__description__ = "Michael J. Harms"
__date__ = "2016-05-20"

import serial, re, os

import PyCmdMessenger
from .. import RobotDevice

class ArduinoRobotDevice(RobotDevice):
    """
    Base class for a RobotDevice that uses an arduino.
    """

    def __init__(self,
                 internal_device_name=None,
                 commands=(),
                 baud_rate=9600,
                 device_tty=None,
                 name=None):
        """
        The modified __init__ function attempts to connect to the arduino device.
        It does so by matching "internal_device_name" with the name returned when the 
        command "who_are_you" is sent over the CmdMessenger interface.
        """

        RobotDevice.__init__(self,name)

        self._internal_device_name = internal_device_name
        self._device_tty = device_tty
        self._commands = commands
        self._baud_rate = baud_rate
        self._device_tty = device_tty

        # Status that indicates whether the software device has actually found
        # any hardware.
        self._hardware_is_found = False

        # Try to connect to specified device
        if self._device_tty != None:

            try:
                self._arudino_raw_serial = PyCmdMessenger.ArduinoBoard(self._device_tty,
                                                                       baud_rate=self._baud_rate)
                self._arduino_msg = PyCmdMessenger.CmdMessenger(self._arduino_raw_serial,
                                                                self._commands)
                self._hardware_is_found = True

            except:
                pass

        # Or look for the device
        else:
            self._find_serial()

        # Send message that we've found device (or not)
        if self._hardware_is_found:
            message="{} connected on {} at {} baud.".format(self._internal_device_name,
                                                            self._device_tty,
                                                            self._baud_rate)
            self._queue_message(message)

        else:
            message="Could not find usb device identifying as {}".format(self._internal_device_name)

            self._queue_message(message,destination="warn")  

    def _find_serial(self):
        """
        Search through attached serial devices until one reports the specified
        internal_device_name when probed by "who_are_you".
        """

        # if there is already a serial connection, move on
        if self._hardware_is_found:
            return

        tty_devices = [d for d in os.listdir("/dev") if d.startswith("ttyA")]

        for d in tty_devices:

            try:
                tmp_tty = os.path.join("/dev",d)
                a = PyCmdMessenger.ArduinoBoard(tmp_tty,self._baud_rate)
                cmd = PyCmdMessenger.CmdMessenger(a,self._commands)

                cmd.send("who_are_you")
                reply = cmd.receive()
                if reply != None:
                    if reply[0] == "who_are_you_return":
                        if reply[1][0] == self._internal_device_name:
                            self._arduino_raw_serial = a
                            self._arduino_msg = cmd
                            self._device_tty = tmp_tty
                            self._hardware_is_found = True
                            break

            # something went wrong ... not a device we can use.
            except IndexError:
                pass


    def _not_connected_callback(self):
        """
        This is a callback that should override other callbacks in the event 
        that the device actually isn't connected.  
        """

        msg = "Device {} is not connected.".format(self.name)
        self._queue_message(msg)


