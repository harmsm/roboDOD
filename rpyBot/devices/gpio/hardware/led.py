from . import Pin, OwnershipError

class LED:
    """
    Class for controlling an LED via a single GPIO pin.  Brightness and 
    flashing is controlled by pulse width modulation.
    """

    def __init__(self,pin,frequency=1,duty_cycle=100):
        
        self.pin = Pin(pin,frequency,duty_cycle)
        self.led_on = False

    def on(self,owner):
        """
        Turn LED on.
        """

        self.pin.acquire(owner)
        self.pin.start_pwm(owner)
        self.led_on = True
        self.pin.release(owner)

    def off(self,owner):
        """
        Turn LED off.
        """

        self.pin.acquire(owner)
        self.pin.stop_pwm(owner)
        self.led_on = False
        self.pin.release(owner)
   
    def flip(self,owner):
        """
        Flip state of LED from off->on or on->off.
        """   
 
        self.pin.acquire(owner)

        if self.led_on:
            self.off(owner)
        else:
            self.on(owner)

        self.pin.release(owner)

    def set_frequency(self,frequency,owner):
        """
        Change pulse width modulation frequency.
        """

        self.pin.acquire(owner)

        self.frequency = frequency
        self.pin.set_frequency(self.frequency,owner)

        self.pin.release(owner)

    def set_duty_cycle(self,duty_cycle,owner):
        """
        Change pulse width modulation duty cycle.
        """

        self.pin.acquire(owner)

        self.duty_cycle = duty_cycle
        self.pin.set_duty_cycle(self.duty_cycle,owner)

        self.pin.release(owner)

    def stop(self,owner):
        """
        Shut down the GPIO pin for this LED.
        """
        
        self.pin.stop(owner)       
 
