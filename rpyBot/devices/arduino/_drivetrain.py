
from . import ArduinoRobotDevice

COMMANDS = (("who_are_you",""),
            ("set_speed","dd"),
            ("get_speed",""),
            ("who_are_you_return","s"),
            ("set_speed_return","dd"),
            ("get_speed_return","ddiddi"),
            ("communication_error","s"))

BAUD_RATE = 9600                   
 

class Drivetrain(ArduinoRobotDevice):
    """
    """

    def __init__(self,
                 internal_device_name=None,
                 device_tty=None,
                 name=None):
        """
        """

        super(Drivetrain, self).__init__(internal_device_name,
                                         COMMANDS,
                                         BAUD_RATE,
                                         device_tty,
                                         name)

        self._control_dict = {"forward":self._forward,
                              "reverse":self._reverse,
                              "brake":self._brake,
                              "coast":self._coast,
                              "left":self._left,
                              "right":self._right,
                              "setspeed":self._set_speed}

        if self._hardware_is_found:
            self.state = "coast"
            self._control_dict[self.state]()
        else:
            for k in self._control_dict.keys():
                self._control_dict[k] = self._not_connected_callback

    def _forward(self):

        self.state = "forward"
        self._arduino_msg.send("set_speed",self._drive_speed,self._drive_speed)
        self._queue_message("Set forward speed to {}".format(self._drive_speed))

    def _reverse(self):

        self.state = "reverse"
        self._arduino_msg.send("set_speed",-self._drive_speed,-self._drive_speed)
        self._queue_message("Set reverse speed to {}".format(self._drive_speed))
        
    def _left(self):
    
        self.state = "left" 
        self._arduino_msg.send("set_speed",-self._drive_speed,self._drive_speed)
        self._queue_message("Set left turn speed to {}".format(self._drive_speed))

    def _right(self):

        self.state = "right"
        self._arduino_msg.send("set_speed",self._drive_speed,-self._drive_speed)
        self._queue_message("Set right turn speed to {}".format(self._drive_speed))
        
    def _brake(self):

        self.state = "brake"
        self._arduino_msg.send("set_speed",0,0)
        self._queue_message("Set motors to stopped")
        
    def _coast(self):

        self.state = "coast"
        self._arduino_msg.send("set_speed",0,0)
        self._queue_message("Set motors to stopped")

    def _set_speed(self,speed,owner):
        """
        Set the speed of the motors.
        """
    
        # Make sure the speed set makes sense. 
        if speed > self._max_speed or speed < self._min_speed:
            err = "speed {:.3f} is invalid".format(speed)

            self._queue_message(err,destination_device="warn")

            # Be conservative.  Since we recieved a mangled speed command, set
            # speed to 0.
            self._queue_message("setspeed",{"speed":0},
                                destination="robot",
                                destination_device=self.name)
        else:
            self._drive_speed = speed

        self._arduino_msg.send("set_speed",self._drive_speed)

        
    def shutdown(self,owner):

        pass 
