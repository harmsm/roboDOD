__description__ = \
"""
Base class for allowing communication between the raspberry pi robot controller
and an arduino slave.
"""
__description__ = "Michael J. Harms"
__date__ = "2016-05-20"

import serial, re, os

from devices import RobotDevice
from messages import RobotMessage

class ArduinoRobotDevice(RobotDevice):
    """
    Base class for a RobotDevice that uses an arduino.
    """

    def __init__(self,internal_device_name=None,baud_rate=9600,device_tty=None,name=None):
        """
        The modified __init__ function attempts to connect to the arduino device.
        It does so by matching "internal_device_name" with the name returned when the 
        command "who_are_you" is sent over the CmdMessenger interface.
        """

        RobotDevice.__init__(self,name)

        self._internal_device_name = internal_device_name
        self._device_tty = device_tty

        self.baud_rate = baud_rate
        self.found_device = False

        # Try to connect to specified device
        if self._device_tty != None:
            try:
                self._arduino_messager = PyCmdMessenger.PyCmdMessenver(self._device_tty,
                                                                       command_names=["who_are_you"],
                                                                       baud_rate=self.baud_rate)
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
                                                            self.baud_rate)
            msg = RobotMessage(source_device=self.name,
                               message=message)
            self._messages.append(msg)

        else:
            message="Could not find usb device identifying as {}".format(self._internal_device_name)

            msg = RobotMessage(destination="warn",
                               source_device=self.name,
                               message=message)

            self._messages.append(msg)  
 
        
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
                tmp_msg = CmdMessage(tmp_tty,self.baud_rate)
                tmp_msg.write("who_are_you") 
               
                reported_internal_device_name = tmp_msg.read()

                if reported_internal_device_name[0][1] == self._internal_device_name:
                    self._device_tty = tmp_tty
                    self._device_msg = tmp_msg
                    self.found_device = True
                    break

            except (FileNotFoundError,PermissionError,TypeError):
                pass


