from . import Pin, OwnershipError

class Motor:
    """
    Class for controlling a DC motor via two GPIO pins.  Motor speed can be
    controlled via pulse-width modulation.
    """
    
    def __init__(self,pin1,pin2,frequency=50,duty_cycle=100):
        
        self.pin1 = Pin(pin1,frequency,duty_cycle)
        self.pin2 = Pin(pin2,frequency,duty_cycle)
        self.frequency = frequency
        self.duty_cycle = duty_cycle

        self._current_state = "coast"

    def _acquire(self,owner):
        """
        Acquire locks on both pins, releasing the acquired pin if acquisition
        of the other pin fails.
        """

        try:
            self.pin1.acquire(owner)
            self.pin2.acquire(owner)
        except OwnershipError as err:
            self.pin1.release(owner)
            raise OwnershipError(err)

    def _release(self,owner):
        """
        Release locks on both pins.
        """

        self.pin1.release(owner)
        self.pin2.release(owner)
    
    def forward(self,owner):
        """
        Run motor forward.
        """

        if self._current_state == "forward":
            return None

        self._acquire(owner)

        self.pin1.start_pwm(owner)
        self.pin2.stop_pwm(owner)
        self._current_state = "forward"

        self._release(owner)


    def reverse(self,owner):
        """
        Run motor in reverse.
        """
    
        if self._current_state == "reverse":
            return None

        self._acquire(owner)

        self.pin1.stop_pwm(owner)
        self.pin2.start_pwm(owner)
        self._current_state = "reverse"
        
        self._release(owner)
        
   
    def brake(self,owner):
        """
        Use the motor as a brake by running both pins.
        """

        if self._current_state == "brake":
            return None

        self._acquire(owner)

        self.pin1.start_pwm(owner)
        self.pin2.start_pwm(owner)
        self._current_state = "brake"

        self._release(owner)
        
   
    def coast(self,owner):
        """
        Put motor in coast by stopping both pins.
        """

        if self._current_state == "coast":
            return None
        
        self._acquire(owner)

        self.pin1.stop_pwm(owner)
        self.pin2.stop_pwm(owner)
        self._current_state = "coast"

        self._release(owner)

    def set_duty_cycle(self,duty_cycle,owner):
        """
        Set pulse width modulation duty cycle.
        """

        self._acquire(owner)

        self.duty_cycle = duty_cycle
        self.pin1.set_duty_cycle(self.duty_cycle,owner)
        self.pin2.set_duty_cycle(self.duty_cycle,owner)

        self._release(owner)

    def set_frequency(self,frequency,owner):
        """
        Set pulse width modulation frequency.
        """

        self._acquire(owner)

        self.frequency = frequency
        self.pin1.set_frequency(self.frequency,owner)
        self.pin2.set_frequency(self.frequency,owner)

        self._release(owner)

    def shutdown(self,owner):
        """
        Shut down and clean up the pins.
        """     
 
        self.coast(owner) 
        self.pin1.shutdown(owner)
        self.pin2.shutdown(owner)

