__description__ = \
"""
Low level hardware interfaces to devices plugged into the GPIO pins on the pi.
"""

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

class GPIOMotor:
    
    def __init__(self,pin1,pin2):
        
        self.pin1 = pin1
        self.pin2 = pin2

        GPIO.setup(self.pin1, GPIO.OUT)
        GPIO.setup(self.pin2, GPIO.OUT)

        # http://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/
        # put in pwm control here.
        

    def forward(self):
        GPIO.output(self.pin1, True)
        GPIO.output(self.pin2, False)

    def reverse(self):
        GPIO.output(self.pin1, False)
        GPIO.output(self.pin2, True)

    def stop(self):
        GPIO.output(self.pin1, True)
        GPIO.output(self.pin2, True)
   
    def coast(self):
        GPIO.output(self.pin1, False)
        GPIO.output(self.pin2, False)

class LED:

    def __init__(self,pin):
        
        self.pin = pin

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

        self.led_on = False

    def on(self):

        GPIO.output(self.pin,True)
        self.led_on = True
    

    def off(self):
        
        GPIO.output(self.pin,False)
        self.led_on = False
   
    def flip(self):
    
        if self.led_on:
            self.on()
        else:
            self.off()

    def flash(self,period=1000):
        """
        Flash the LED on and off with period.
        """
    
        for i in range(period):
            self.flip()
            
class UltrasonicRange:

    def __init__(self,trigger_pin,echo_pin,timeout=5000):

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
