
from . import ArduinoRobotDevice

class Drivetrain(ArduinoRobotDevice):
    """
    """

    def __init__(self,device_name=None,baud_rate=9600,device_tty=None,name=None):
        """
        """

        super(ArduinoRobotDevice, self).__init__(device_name,baud_rate,device_tty,name)

        self._control_dict = {"forward":self._forward,
                              "reverse":self._reverse,
                              "brake":self._brake,
                              "coast":self._coast,
                              "left":self._left,
                              "right":self._right,
                              "setspeed":self._set_speed}

    def _forward(self,owner):

        self._arduino.write(CMD_SET_SPEED,self._drive_speed,self._drive_speed)
        self._send_msg("Set forward speed to {}".format(self._drive_speed))

    def _reverse(self,owner):

        self._arduino.write(CMD_SET_SPEED,-self._drive_speed,-self._drive_speed)
        self._send_msg("Set reverse speed to {}".format(self._drive_speed))
        
    def _left(self,owner):
     
        self._arduino.write(CMD_SET_SPEED,-self._drive_speed,self._drive_speed)
        self._send_msg("Set left turn speed to {}".format(self._drive_speed))

    def _right(self,owner):

        self._arduino.write(CMD_SET_SPEED,self._drive_speed,-self._drive_speed)
        self._send_msg("Set right turn speed to {}".format(self._drive_speed))
        
    def _brake(self,owner):

        self._arduino.write(CMD_SET_SPEED,0,0)
        self._send_msg("Set motors to stopped")
        
    def _coast(self,owner):

        self._arduino.write(CMD_SET_SPEED,0,0)
        self._send_msg("Set motors to stopped")

    def _set_speed(self,speed,owner):
        """
        Set the speed of the motors.
        """
    
        # Make sure the speed set makes sense. 
        if speed > self._max_speed or speed < 0:
            err = "speed {:.3f} is invalid".format(speed)

            self._send_msg(err,destination_device="warn")

            # Be conservative.  Since we recieved a mangled speed command, set
            # speed to 0.
            self._send_msg(["setspeed",{"speed":0}],
                                 destination="robot",
                                 destination_device=self.name)
        else:
            self._drive_speed = speed

        self._arduino_msg.send("set_speed",self._drive_speed)

        
    def shutdown(self,owner):

        pass 
