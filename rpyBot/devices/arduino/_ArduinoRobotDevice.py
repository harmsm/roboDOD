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
                 command_names=(),
                 command_formats=(),
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
        self._command_names = command_names
        self._command_formats = command_formats
        self._baud_rate = baud_rate
        self._device_tty=device_tty

        self.found_device = False

        # Try to connect to specified device
        if self._device_tty != None:
            try:
                self._arudino_board = PyCmdMessenger.ArduinoBoard(self._device_tty,
                                                                  baud_rate=self._baud_rate)

                self._arduino_msg = PyCmdMessenger.CmdMessenger(self._arduino_board,
                                                                command_names=self._command_names,
                                                                command_formats=self._command_formats)
                self.found_device = True

            except:
                pass

        # Or look for the device
        else:
            self._find_serial()

        # Send message that we've found device (or not)
        if self.found_device:
            message="{} connected on {} at {} baud.".format(self._internal_device_name,
                                                            self._device_tty,
                                                            self._baud_rate)
            self._send_msg(message)

        else:
            message="Could not find usb device identifying as {}".format(self._internal_device_name)

            self._send_msg(message,destination="warn")  
 
        
    def _find_serial(self):
        """
        Search through attached serial devices until one reports the specified
        internal_device_name when probed by "who_are_you".
        """

        tty_devices = [d for d in os.listdir("/dev") if d.startswith("ttyA")]

        self.found_device = False
        for d in tty_devices:

            try:
                
                tmp_tty = os.path.join("/dev",d)
                tmp_a = PyCmdMessenger.Arduino(tmp_tty,self.baud_rate)
                tmp_msg = PyCmdMessenger.CmdMessenger(tmp_a,
                                                      command_names=self.command_names,
                                                      command_formats=self.command_formats)

                tmp_msg.send("who_are_you") 
                reported_name = tmp_msg.receive()
                if reported_name != None:
                    if reported_name[1][0] == self._internal_device_name:
                        self._arduino_board = tmp_a
                        self._arduino_msg = tmp_msg
                        self.found_device = True
                        break

            except (FileNotFoundError,PermissionError,TypeError):
                pass


