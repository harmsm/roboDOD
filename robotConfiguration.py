__description__ = \
"""
Holds the current configuration of the robot.  This is declared as a simple
list instances of the RobotDevice class (and its derivatives).  Each class has
takes enough information in its __init__ function to specify the current 
hardware configuration.
"""

from robotDevices import *

device_list = [
               TwoMotorCatSteer(left_pin1=15,left_pin2=13,right_pin1=11,right_pin2=7,name="drivetrain"),
               RangeFinder(trigger_pin=16,echo_pin=18,name="forward_range",timeout=10000),
               LEDIndicatorLight(control_pin=19,name="system_up_light"),
               LEDIndicatorLight(control_pin=10,name="attention_light",frequency=1,duty_cycle=50),
               LEDIndicatorLight(control_pin=12,name="client_connected_light"),
]
