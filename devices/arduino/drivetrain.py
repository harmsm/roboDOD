
from messages import RobotMessage
from . import ArduinoRobotDevice

class ArduinoDrivetrain(ArduinoRobotDevice):
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

        self._arduino_messager = PyCmdMessage.PyCmdMessage(self.device_tty

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

        self._arduino_msg.send("set_speed",self._drive_speed)

        
    def shutdown(self,owner):

        pass 
