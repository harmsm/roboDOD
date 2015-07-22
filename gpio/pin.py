
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(10)

import multiprocessing
global_pin_owners = [-1 for i in range(num_pins)]
global_pin_lock = multiprocessing.Rlock()

class OwnershipError(Exception):
    """
    Errors in the ownership of a given gpio pin (such as two threads trying to
    control a pin simultaneously). 
    """

    pass 


class Pin:
    """
    Class that, in conjunction with global_pin_owners and global_pin_lock,
    provides thread-safe access to GPIO functionality.  Each Pin can only be
    controlled by a single owner--defined by an integer--at a single time. 
    """

    def __init__(self,pin_number,frequency=50,duty_cycle=100):

        self.pin_number = pin_number
        self.duty_cycle = duty_cycle
        self.frequency = frequency
  
        self._pwm = None
        self._initialize()


    def acquire(self,owner):
        """
        Acquire ownership of a pin.
        """

        with global_pin_lock:

            if global_pin_owner[self.pin_number] == -1:
                self._initialize()
                global_pin_owners[self.pin_number] = owner

            elif global_pin_owners[self.pin_number] == 0:
                global_pin_owners[self.pin_number] = owner

            else:
                err = "pin {:d} owned by {:d}, not {:d}\n".format(
                    self.pin_number,global_pin_owners[self.pin_number],owner)
                raise OwnershipError(err)   
 
    def release(self,owner):
        """
        Release a pin.  Don't throw an error if "owner" doesn't really own 
        the pin because the end state (pin-not-owned-by-owner) is the same.
        """       
 
        with global_pin_lock:
            if global_pin_owners[self.pin_number] == owner:
                global_pin_owners[self.pin_number] = 0
    
    def up(self,owner):
        """
        Put a pin in the "up" state.
        """

        if pin_owners[self.pin_number] == owner:
            GPIO.output(self.pin_number,True)
        else:
            err = "pin {:d} owned by {:d}, not {:d}\n".format(
                self.pin_number,global_pin_owners[self.pin_number],owner)
            raise OwnershipError(err)   

    def down(self,owner):
        """
        Put a pin in the "down" state.
        """

        if pin_owners[self.pin_number] == owner:
            GPIO.output(self.pin_number,False)
        else:
            err = "pin {:d} owned by {:d}, not {:d}\n".format(
                self.pin_number,global_pin_owners[self.pin_number],owner)
            raise OwnershipError(err)   
      
    def input(self,owner):
        """
        Read the state of a pin.
        """

        if pin_owners[self.pin_number] == owner:
            return GPIO.input(self.pin_number)
        else:
            err = "pin {:d} owned by {:d}, not {:d}\n".format(
                self.pin_number,global_pin_owners[self.pin_number],owner)
            raise OwnershipError(err)   

    def start_pwm(self,owner):
        """
        Start pulse width modulation running (using self.frequency and
        self.duty_cycle).
        """

        if global_pin_owners[self.pin_number] == owner:

            self._pwm = GPIO.PWM(self.pin_number,self.frequency)
            self._pwm.start(self.duty_cycle)

        else:
            err = "pin {:d} owned by {:d}, not {:d}\n".format(
                self.pin_number,global_pin_owners[self.pin_number],owner)
            raise OwnershipError(err)   
    
    def stop_pwm(self,owner):
        """
        Stop pulse width modulation.  (Doesn't throw an error if it wasn't 
        running in the first place).
        """

        if global_pin_owners[self.pin_number] == owner:

            if self._pwm != None:
                self._pwm.stop()    
                self._pwm = None

        else:
            err = "pin {:d} owned by {:d}, not {:d}\n".format(
                self.pin_number,global_pin_owners[self.pin_number],owner)
            raise OwnershipError(err)   
        
    def change_frequency(self,frequency,owner):
        """
        Change pulse width modulation frequency.  If PWM is already running, it
        will be stopped and restarted with the new frequency.
        """
 
        if global_pin_owners[self.pin_number] == owner: 

            self.frequency = frequency
            if self._pwm != None:
                self.stop_pwm(owner)
                self.start_pwm(owner)

        else:
            err = "pin {:d} owned by {:d}, not {:d}\n".format(
                self.pin_number,global_pin_owners[self.pin_number],owner)
            raise OwnershipError(err)   

    def change_duty_cycle(self,duty_cycle,owner):
        """
        Change pulse width modulation duty cycle.  If PWM is already running, it
        will be stopped and restarted with the new duty cycle.
        """
        
        if global_pin_owners[self.pin_number] == owner: 

            self.duty_cycle = duty_cycle
            if self._pwm != None:
                self.stop_pwm(owner)
                self.start_pwm(owner)

        else:
            err = "pin {:d} owned by {:d}, not {:d}\n".format(
                self.pin_number,global_pin_owners[self.pin_number],owner)
            raise OwnershipError(err)   

    def shutdown(self,owner):
        """
        Shutdown a gpio pin, cleaning up.  This operation will automatically 
        release the lock.
        """

        with global_pin_lock:
            if global_pin_owners[self.pin_number] == owner:
                GPIO.cleanup(self.pin_number)

                # Record that the pin is cleaned up.  This will also
                # release the pin.
                global_pin_owners[self.pin_number] = -1

    def _initialize(self):
        """
        Initialize a pin (called by acquire or __init__, but not public).
        """
 
        with global_pin_lock:

            # If the pin has not been initialized (global_pin_owners[pin] == -1),
            # initailize it
            if global_gpio_owners[self.pin_number] == -1:
                GPIO.setup(self.pin_number, GPIO.OUT)
                self.down(owner=-1)
                global_gpio_owners[self.pin_number] = 0
            else:
                err = "pin {:d} already under control of another gpio.Pin instance\n".format(self.pin_number)
                raise OwnershipError(err)

