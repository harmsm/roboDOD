import time
from . import Pin, OwnershipError

class UltrasonicRange:
    """
    Class for controlling an ultrasonic range finder via two gpio pins (a 
    trigger pin that sends out a pulse and a echo pin that recieves the return).
    """

    def __init__(self,trigger_pin,echo_pin,timeout=50000):

        self.trigger_pin = Pin(trigger_pin)
        self.echo_pin = Pin(echo_pin,as_input=True)

        self.timeout = timeout

        # Allow module to settle
        time.sleep(0.5)
    
    def _acquire(self,owner):
        """
        Acquire ownership of the pins.
        """

        try:
            self.trigger_pin.acquire(owner)
            self.echo_pin.acquire(owner)
        except OwnershipError as err:
            self.trigger_pin.release(owner)
            raise OwnershipError(err)

    def _release(self,owner):
        """
        Release ownership of the pins.
        """

        self.trigger_pin.release(owner)
        self.echo_pin.release(owner)

    def get_range(self,owner):
        """
        Calculate the distance to a target based on the length of the return
        echo. Returns a negative value of the system times out.
        """

        self._acquire(owner)

        # Send 10 us pulse trigger
        self.trigger_pin.up(owner)
        time.sleep(0.00001)
        self.trigger_pin.down(owner)

        # Find start of echo
        counter = 0 
        start = time.time()
        while self.echo_pin.input(owner) == 0 and counter < self.timeout:
            start = time.time()
            counter += 1

        if counter == self.timeout:
            self._release(owner)
            return -1.0

        # Find end of echo
        counter = 0 
        stop = time.time()
        while self.echo_pin.input(owner) == 1 and counter < self.timeout:
            stop = time.time()
            counter += 1

        if counter == self.timeout:
            self._release(owner)
            return -1.

        self._release(owner)

        # multiply high time by 340 m/s divided by 2 (ping went there and back)
        # to give distance in m
        return (stop - start)*170

    def stop(self,owner):
        """
        Shut down and clean up the pins.
        """     
 
        self.trigger_pin.stop(owner)
        self.echo_pin.stop(owner)
        
