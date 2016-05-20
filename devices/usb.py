
import time

import gpio
from . import RobotDevice
from messages import RobotMessage


class USBRobotDevice(RobotDevice):
    """
    """

    def __init__(self,device_name=None,baud_rate=9600,device_tty=None,name=None):
        """
        """

        RobotDevice.__init__(self,name)

        self._device_name = device_name
        self.baud_rate = baud_rate
        self._device_tty = device_tty

        self.found_device = False

        if self._device_tty != None:
            try:       
                self._device_handle = serial.Serial(self._device_tty,self.baud_rate)
                self.found_device = True
            except:
                pass

        else:
            self._find_serial()

        if self.found_device:
            message="{} connected on {} at {} baud.".format(self._device_name,
                                                            self._device_tty,
                                                            self.baud_rate))
            msg = RobotMessage(source_device=self.name,
                               message=message)
            self._messages.append(msg)

        else:
            message="Could not find usb device identifying as {}".format(self._device_name)

            msg = RobotMessage(destination="warn",
                               source_device=self.name,
                               message=message)

            self._messages.append(msg)  
 
        

    def _find_serial(self):
        """
        Search through attached serial devices until one reports the specified
        device_name when probed by "who_are_you".
        """

        tty_devices = [d for d in os.listdir("/dev") if d.startswith("ttyA")]

        self.found_device = False
        for d in tty_devices:

            try:
                
                tmp_tty = os.path.join("/dev",d)
                tmp_handle = serial.Serial(tmp_tty,self.baud_rate)
                tmp_handle.write("who_are_you")
               
                reported_device_name = tmp_handle.read()

                if reported_device_name == self._device_name:
                    self._device_handle = tmp_handle
                    self._device_tty = tmp_tty
                    self.found_device = True
                    break

            # MAKE THIS BETTER EXCEPTION HANDLING...
            except:
                pass


def ArduinoDrivetrain(USBRobotDevice):
    """
    """

    def __init__(self,device_name=None,baud_rate=9600,device_tty=None,name=None):
        """
        """

        super(ArduinoDrivetrain, self).__init__(device_name,baud_rate,device_tty,name)

        self._control_dict = {"forward":self._forward,
                              "reverse":self._reverse,
                              "brake":self._brake,
                              "coast":self._coast,
                              "left":self._left,
                              "right":self._right,
                              "setspeed":self._set_speed}

    def _forward(self,owner):

        pass

    def _reverse(self,owner):

        pass
        
    def _left(self,owner):
     
        pass 

    def _right(self,owner):

        pass
        
    def _brake(self,owner):

        pass
        
    def _coast(self,owner):

        pass

    def _set_speed(self,speed,owner):
        """
        Set the speed of the motors.
        """
    
        # Make sure the speed set makes sense. 
        if speed > self._max_speed or speed < 0:
            err = "speed {:.3f} is invalid".format(speed)

            self._append_message(RobotMessage(destination_device="warn",
                                              source_device=self.name,
                                              message=err))

            # Be conservative.  Since we recieved a mangled speed command, set
            # speed to 0.
            self._append_message(RobotMessage(destination="robot",
                                              destination_device=self.name,
                                              source="robot",
                                              source_device=self.name,
                                              message=["setspeed",{"speed":0}]))
        else:
            self._drive_speed = speed

        
    def shutdown(self,owner):

        pass 
