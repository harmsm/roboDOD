
from . import ArduinoRobotDevice

COMMAND_NAMES = ("who_are_you",
                 "set_speed",
                 "get_speed",
                 "who_are_you_return",
                 "set_speed_return",
                 "get_speed_return",
                 "communication_error")

COMMAND_FORMATS = ("","ff","","s","ff","ffffff","s")

BAUD_RATE = 9600                   
 

class Drivetrain(ArduinoRobotDevice):
    """
    """

    def __init__(self,
                 internal_device_name=None,
                 command_names=COMMAND_NAMES,
                 command_formats=COMMAND_FORMATS,
                 baud_rate=BAUD_RATE,
                 device_tty=None,
                 name=None):
        """
        """

        super(ArduinoRobotDevice, self).__init__(internal_device_name,
                                                 command_names,
                                                 command_formats,
                                                 baud_rate,
                                                 device_tty,
                                                 name)

        self._control_dict = {"forward":self._forward,
                              "reverse":self._reverse,
                              "brake":self._brake,
                              "coast":self._coast,
                              "left":self._left,
                              "right":self._right,
                              "setspeed":self._set_speed}

        self.state = "coast"
        self._control_dict[state]() 

    def _forward(self):

        self.state = "forward"
        self._arduino_msg.send("set_speed",self._drive_speed,self._drive_speed)
        self._send_msg("Set forward speed to {}".format(self._drive_speed))

    def _reverse(self):

        self.state = "reverse"
        self._arduino_msg.send("set_speed",-self._drive_speed,-self._drive_speed)
        self._send_msg("Set reverse speed to {}".format(self._drive_speed))
        
    def _left(self):
    
        self.state = "left" 
        self._arduino_msg.send("set_speed",-self._drive_speed,self._drive_speed)
        self._send_msg("Set left turn speed to {}".format(self._drive_speed))

    def _right(self):

        self.state = "right"
        self._arduino_msg.send("set_speed",self._drive_speed,-self._drive_speed)
        self._send_msg("Set right turn speed to {}".format(self._drive_speed))
        
    def _brake(self):

        self.state = "brake"
        self._arduino_msg.send("set_speed",0,0)
        self._send_msg("Set motors to stopped")
        
    def _coast(self):

        self.state = "coast"
        self._arduino_msg.send("set_speed",0,0)
        self._send_msg("Set motors to stopped")

    def _set_speed(self,speed,owner):
        """
        Set the speed of the motors.
        """
    
        # Make sure the speed set makes sense. 
        if speed > self._max_speed or speed < self._min_speed:
            err = "speed {:.3f} is invalid".format(speed)

            self._send_msg(err,destination_device="warn")

            # Be conservative.  Since we recieved a mangled speed command, set
            # speed to 0.
            self._send_msg("setspeed",{"speed":0},
                            destination="robot",
                            destination_device=self.name)
        else:
            self._drive_speed = speed

        self._arduino.send("set_speed",self._drive_speed)

        
    def shutdown(self,owner):

        pass 
