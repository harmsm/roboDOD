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
               arduino.Drivetrain(internal_device_name="MOTOR_SPEED_CONTROLLER",name="drivetrain"),
               #gpio.RangeFinder(trigger_pin=16,echo_pin=18,name="forward_range",timeout=10000),
               gpio.IndicatorLight(control_pin=8,name="system_up_light"),
               gpio.IndicatorLight(control_pin=12,name="attention_light",frequency=1,duty_cycle=50),
               gpio.LightTower(control_pins=(16,18,22,24),name="light_tower"),
               web.WebInterface(8081,name="controller"),
]

