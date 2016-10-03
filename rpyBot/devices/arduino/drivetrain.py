__description__ = \
"""
Arudino device for controlling a cat-style drive train. 
"""
__author__ = "Michael J. Harms"
__date__ = "2016-09-26"

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
    Class for interfacing with an arduino drivetrain that has two motors 
    arranged "cat" style.  
    """

    def __init__(self,
                 internal_device_name=None,
                 device_tty=None,
                 name=None,
                 speed_limits=(0,2),
                 user_unit_to_rps=0.7596357):
        """
        speed_limits: min and max speed in useful user units (defaults are 
                      0 to 2)
        user_unit_to_rps: conversion factor for transforming user units into 
                          wheel rotations per second.
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
                              "setspeed":self._set_speed,
                              "getspeed":self._get_speed}

        self._drive_set_speed = 0
        self._min_speed = speed_limits[0]
        self._max_speed = speed_limits[1]
        self._user_unit_to_rps = user_unit_to_rps

        if self._hardware_is_found:
            self.state = "coast"
            self._control_dict[self.state]()
        else:
            for k in self._control_dict.keys():
                self._control_dict[k] = self._not_connected_callback

    def _speed_to_arduino(self,m0,m1):
        """
        Send a speed command to the arduino, verifying that the command was
        properly recieved.
        """

        self._arduino_msg.send("set_speed",m0,m1)

        reply = self._arduino_msg.receive()
        if reply is not None and reply[0] == "set_speed_return":
            self._queue_message("Set speed to {}, {}".format(reply[1][0]/self._user_unit_to_rps,
                                                             reply[1][1]/self._user_unit_to_rps))
            return
        
        self._queue_message("Received unexpected reply when setting speed ({}).".format(reply),destination_device="warn")
    
    def _forward(self,owner=None):
        """
        Put motors in both-forward state.
        """

        self.state = "forward"
        self._speed_to_arduino(self._drive_set_speed,self._drive_set_speed)
        self._queue_message("Set forward speed to {}".format(self.user_set_speed))

    def _reverse(self,owner=None):
        """
        Put motors in both-reverse state.
        """

        self.state = "reverse"
        self._speed_to_arduino(-self._drive_set_speed,-self._drive_set_speed)
        self._queue_message("Set reverse speed to {}".format(self.user_set_speed))

        
    def _left(self,owner=None):
        """
        Put left motor in forward state, right motor in reverse state.
        """
    
        self.state = "left" 
        self._speed_to_arduino(-self._drive_set_speed,self._drive_set_speed)
        self._queue_message("Set left turn speed to {}".format(self.user_set_speed))

    def _right(self,owner=None):
        """
        Put right motor in reverse state, left motor in forward state.
        """

        self.state = "right"
        self._speed_to_arduino(self._drive_set_speed,-self._drive_set_speed)
        self._queue_message("Set right turn speed to {}".format(self.user_set_speed))
        
    def _brake(self,owner=None):
        """
        Put both motors in stopped state.
        """

        self.state = "brake"
        self._speed_to_arduino(0,0)
        self._queue_message("Set motors to stopped")
        
    def _coast(self,owner=None):
        """
        Put both motors in stopped state (same as braked, kept for legacy calls)
        """

        self.state = "coast"
        self._speed_to_arduino(0,0)
        self._queue_message("Set motors to stopped")

    def _set_speed(self,speed,owner=None):
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
            self._drive_set_speed = speed*self._user_unit_to_rps

        self._control_dict[self.state]()


    def _get_speed(self,owner=None):
        """
        Get the current speed of the motors, as measured on the arduino.
        """

        self._arduino_msg.send("get_speed")
        reply = self._arduino_msg.receive()
 
        if reply is not None and reply[0] == "get_speed_return":
            print(reply)
            m0_speed = reply[1][1]
            m1_speed = reply[1][4]
            
            self._queue_message("Estimated motor speeds: {:.3f} {:.3f}".format(m0_speed,m1_speed))
            return 
            
        self._queue_message("Received unexpected reply when getting speed.",
                            destination_device="warn")
 
    @property
    def user_set_speed(self):
        """
        Return the set speed in the user units.
        """

        return self._drive_set_speed/self._user_unit_to_rps
