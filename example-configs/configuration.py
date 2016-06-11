__description__ = \
"""
Holds the current configuration of the robot.  This is declared as a simple
list instances of the RobotDevice class (and its derivatives).  Each class has
takes enough information in its __init__ function to specify the current 
hardware configuration.
"""

import rpyBot
from rpyBot.devices import arduino, gpio, web

device_list = [
               #gpio.TwoMotorCatSteer(left_pin1=15,left_pin2=13,right_pin1=11,right_pin2=7,name="drivetrain"),
               arduino.Drivetrain(name="drivetrain"),
               gpio.RangeFinder(trigger_pin=16,echo_pin=18,name="forward_range",timeout=10000),
               gpio.IndicatorLight(control_pin=8,name="system_up_light"),
               gpio.IndicatorLight(control_pin=12,name="attention_light",frequency=1,duty_cycle=50),
               gpio.IndicatorLight(control_pin=10,name="client_connected_light"),
               web.WebInterface(8081,"controller")
]
