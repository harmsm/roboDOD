__description__ = \
"""
Holds the current configuration of the robot.  This is declared as a simple
list instances of the RobotDevice class (and its derivatives).  Each class has
takes enough information in its __init__ function to specify the current 
hardware configuration.
"""

from robotDevices import *

# XXX hack
device_list = [
                #TwoMotorCatSteer(left_pin1=15,left_pin2=13,right_pin1=11,right_pin2=7,name="drivetrain"),
                #RangeFinder(trigger_pin=18,echo_pin=16,name="forward_range",timeout=100000),
                #LEDIndicatorLight(control_pin=XX,name="connection_status"),
                #LEDIndicatorLight(control_pin=XX,name="system_up"),
                #LEDIndicatorLight(control_pin=XX,name="attention_light"),
                #Accelerometer(port=1,name="accelerometer")
#               GPIOMotor(pin1=13,pin2=15,name="drive_motor")
#               GPIOMotor(pin1=7,pin2=11,name="steering_motor")
]
