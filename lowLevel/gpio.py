__description__ = \
"""
Low level hardware interfaces to devices plugged into the GPIO pins on the pi.
"""

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

class GPIOMotor:
    """
    Class for controlling a DC motor via two GPIO pins.  Motor speed can be
    controlled via pulse-width modulation.
    """
    
    def __init__(self,pin1,pin2,frequency=50,duty_cycle=100):
        
        self.pin1 = pin1
        self.pin2 = pin2
        self.frequency = frequency
        self.duty_cycle = duty_cycle

        GPIO.setup(self.pin1, GPIO.OUT)
        GPIO.setup(self.pin2, GPIO.OUT)

        self.pin1_pwm = GPIO.PWM(self.pin1,self.frequency)
        self.pin2_pwm = GPIO.PWM(self.pin2,self.frequency)

        self.coast()

    def forward(self):

        self.pin1_pwm = GPIO.PWM(self.pin1,self.frequency)
        self.pin1_pwm.start(self.duty_cycle)
        self.pin2_pwm.stop()

    def reverse(self):
        self.pin1_pwm.stop()
        self.pin2_pwm = GPIO.PWM(self.pin2,self.frequency)
        self.pin2_pwm.start(self.duty_cycle)

    def stop(self):

        self.pin1_pwm = GPIO.PWM(self.pin1,self.frequency)
        self.pin2_pwm = GPIO.PWM(self.pin2,self.frequency)
        self.pin1_pwm.start(self.duty_cycle)
        self.pin2_pwm.start(self.duty_cycle)
   
    def coast(self):

        self.pin1_pwm.stop()
        self.pin2_pwm.stop()

    def setPWMDutyCycle(self,duty_cycle):

        self.duty_cycle = duty_cycle

        self.pin1_pwm.ChangeDutyCycle(self.duty_cycle)
        self.pin2_pwm.ChangeDutyCycle(self.duty_cycle)
    
    def setPWMFrequency(self,frequency):

        self.frequency = frequency

        self.pin1_pwm.ChangeFrequency(self.frequency)
        self.pin2_pwm.ChangeFrequency(self.frequency)

    def shutdown(self):
       
        self.coast() 
        self.pin1_pwm.stop()
        self.pin2_pwm.stop()

class GPIOLED:
    """
    Class for controlling an LED via a single GPIO pin.  Brightness and 
    flashing is controlled by pulse width modulation.
    """

    def __init__(self,pin,frequency=1,duty_cycle=100):
        
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = duty_cycle

        GPIO.setup(self.pin, GPIO.OUT)

        self.pwm = GPIO.PWM(self.pin,self.frequency)
        self.pwm.stop()

        self.led_on = False

    def on(self):

        self.pwm = GPIO.PWM(self.pin,self.frequency)
        self.pwm.start(self.duty_cycle) 
        self.led_on = True
    

    def off(self):
        
        self.pwm.stop()
        self.led_on = False
   
    def flip(self):
    
        if self.led_on:
            self.off()
        else:
            self.on()

    def setPWMFrequency(self,frequency):

        self.frequency = frequency
        self.pwm.ChangeFrequency(self.frequency)
 

    def setPWMDutyCycle(self,duty_cycle):

        self.duty_cycle = duty_cycle
        self.pwm.ChangeDutyCycle(self.duty_cycle)
        
    def shutdown():

        self.off()
        self.pwm.stop()
 
class UltrasonicRange:
    """
    Class for controlling an ultrasonic range finder via two gpio pins (a 
    trigger pin that sends out a pulse and a echo pin that recieves the return).
    """

    def __init__(self,trigger_pin,echo_pin,timeout=50000):

        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.timeout = timeout

        # Set pins as output and input
        GPIO.setup(self.trigger_pin,GPIO.OUT,initial=False)  # Trigger
        GPIO.setup(self.echo_pin,GPIO.IN,initial=False)      # Echo

        # Allow module to settle
        time.sleep(0.5)

    def getRange(self):
        """
        Calculate the distance to a target based on the length of the return
        echo. Returns a negative value of the system times out.
        """

        # Send 10 us pulse trigger
        GPIO.output(self.trigger_pin,True)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin,False)

        # Find start of echo
        counter = 0 
        start = time.time()
        while GPIO.input(self.echo_pin)==0 and counter < self.timeout:
            start = time.time()
            counter += 1

        if counter == self.timeout:
            return -1.0

        # Find end of echo
        counter = 0 
        stop = time.time()
        while GPIO.input(self.echo_pin)==1 and counter < self.timeout:
            stop = time.time()
            counter += 1

        if counter == self.timeout:
            return -1.

        # multiply high time by 340 m/s divided by 2 (ping went there and back)
        # to give distance in m
        return (stop - start)*170
