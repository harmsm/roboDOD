__description__ = \
"""
Holds the current configuration of the robot.  This is declared as a simple
list instances of the RobotDevice class (and its derivatives).  Each class has
takes enough information in its __init__ function to specify the current 
hardware configuration.
"""

from robotDevices import *

device_list = [
                TwoMotorDriveSteer(drive_pin1=13,drive_pin2=15,steer_pin1=7,steer_pin2=11,name="drivetrain"),
                RangeFinder(trigger_pin=18,echo_pin=16,name="forward_range",timeout=100000)        
#               GPIOMotor(pin1=13,pin2=15,name="drive_motor")
#               GPIOMotor(pin1=7,pin2=11,name="steering_motor")
]
