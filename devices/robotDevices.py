__description__ = \
"""
These classes, built on the base-class RobotDevice, are used to provide the
hardware-specific functions required for each device.  Each class has six 
public methods:

connectManager: put device under exclusive control of a DeviceManager instance
disconnectManager: drop current controlling DeviceManager instance
get: get any messages since last polled, clearing messages
put: send a command to the device (via private methods in _control_dict)
get_now: return data from device directly, skipping asynchrony
shutdown: safely shutdown the hardware

All other methods should private and controlled via the put() method. put takes
a command of the form:

    "key" OR
    ["key",{kwarg1:value1,kwarg2:value2...}"]

When writing methods, all functions should access self._messages via the 
self._append_message and self._get_messages methods, as these use a re-enterant
thread lock to stay thread-safe.  This is critical because the tornado server
and device manager are on different threads but can both post messages.
""" 
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

from random import random
from lowLevel import *
from robotMessages import *
import time, threading

class RobotDevice:
    """
    Base class for connecting to low-level device functionality.  
    """

    def __init__(self,name=None):
        """
        Initialize the device.
        """

        # Give the devivce a unique name
        if name != None:
            self.name = name
        else:
            self.name = "{:s}{.3f}".format(self.__class__.__name__,time.time())

        self._control_dict = {}
        self._manager = None

        self._lock = threading.RLock()
        self._messages = []

    def connectManager(self,manager):
        """
        Connect this device to requesting manager, unless we're already connected
        elsewhere.

        on error, return string.  Otherwise, return None.
        """

        if self._manager != None:
            err = "{:s} already under control of {:s}".format(self.name,
                                                              self._manager)
            return err
        else:       
            self._manager = manager
   
        return None
 
    def disconnectManager(self):
        """
        Drop the connection to the manager.
        """      
 
        self._manager = None 

    def get(self):
        """
        Function to poll this piece of hardware for new messages to pass to the 
        manager.
        """

        return self._get_all_messages()
    

    def put(self,command,owner):
        """
        Send a commmand to the device.  Expects to have structure:

            message = "key_for_control_dict~{kwarg1:value1,kward2:value2...}"

        and is parsed like:

            self._control_dict[key_for_control_dict](**kwargs)
        """

        try:

            # kwargs are specified, parse!
            if type(command) == list:
                try:
                    function_key = command[0]
                    kwargs = command[1]
                    self._control_dict[function_key](owner=owner,**kwargs)
                except:
                    err = "Mangled command ({:s})".format(command)
                    self._append_message(RobotMessage(destination_device="warn",
                                                      source_device=self.name,
                                                      message=err))

            # No kwargs specified         
            else:
                self._control_dict[command](owner=owner)

            # Send the message we just processed back to the controller.
            self._append_message(RobotMessage(source_device=self.name,
                                              message=command))


        # ownership collision, try again on next pass
        except OwnershipError:
            self._append_message(RobotMessage(destination="robot",
                                              destination_device=self.name,
                                              message=command))

        # Problem somewhere.
        except:
            err = "Command {:s} failed for {:s}. Trying again.".format(command,
                                                                       self.__class__.__name__)
            self._append_message(RobotMessage(destination_device="warn",
                                              source_device=self.name,
                                              message=err))
 
    def get_now(self,command,owner):
        """
        Return value immediately; forget that asynchronous stuff.
        """
        
        return None
 
    def shutdown(self,owner):
        """
        Safely shut down the piece of hardware.  
        """

        pass

    def _append_message(self,msg):
        """
        Append to self._messages in a thread-safe manner.
        """

        with self._lock:
            self._messages.append(msg)

    def _get_all_messages(self):
        """
        Get all self._messages (wiping out existing) in a thread-safe manner.
        """

        with self._lock:

            m = []
            if len(self._messages) > 0:
                m = self._messages[:]
                self._messages = []

            return m

class DummyDevice(RobotDevice):
    """
    This is a virtual device for dealing with general messages that apply to 
    all devices, etc.
    """

    def __init__(self,name=None):

        RobotDevice.__init__(self,name)

    def put(self,command):
        """
        This dummy function basically echoes the command back to the 
        device manager.
        """

        self._append_message(RobotMessage(source_device=self.name,
                                          message=command))

class SingleMotor(RobotDevice):
    """
    Single gpio.Motor under control of two GPIO pins.
    """
 
    def __init__(self,pin1,pin2,duty_cycle=100,frequency=50,name=None):
        """
        Initialize the motor, defining an allowable set of commands, as well as
        the gpio pins.  

        control_dict:
        forward: motor going forward, no kwargs
        reverse: motor going in reverse, no kwargs
        brake: use the motor as a brake, no kwargs
        coast: disengage the motor, no kwargs
        set_dutycyle: set the PWM duty cycle, kwargs = {"duty_cycle":float}
        set_freq: set PWM frequency, kwargs = {"frequency":float}
        """

        RobotDevice.__init__(self,name)

        self._motor = gpio.Motor(pin1,pin2,
                                 duty_cycle=duty_cycle,
                                 frequency=frequency)

        self._control_dict = {"forward":self._motor.forward,
                              "reverse":self._motor.reverse,
                              "break":self._motor.brake,
                              "coast":self._motor.coast,
                              "set_dutycycle":self._motor.set_duty_cycle,
                              "set_freq":self._motor.set_frequency}

    def shutdown(self,owner):
        """
        Shut down the motor.
        """

        self._motor.coast(owner)


class TwoMotorDriveSteer(RobotDevice):
    """
    Two GPIOMotors that work in synchrony.  The drive motor does forward and 
    reverse, the steer motor moves the wheels left and right.
    """ 
 
    def __init__(self,drive_pin1,drive_pin2,steer_pin1,steer_pin2,name=None,
                 left_return_constant=0.03,right_return_constant=0.03):
        """
        Initialize the motors.

        drive and steering pins are GPIO pins.
        return constants define how long to run motors to bring back from hard
            left and right steers, respectively.

        control_dict:
        forward: drive motor going forward, no kwargs
        reverse: drive motor going in reverse, no kwargs
        brake: use the motor as a brake, no kwargs
        coast: disengage the drive motor, no kwargs
        left: steer motor left, no kwargs
        right: steer motor right, no kwargs
        center: steer motor center, no kwargs
        """

        RobotDevice.__init__(self,name)

        self._drive_motor = gpio.Motor(drive_pin1,drive_pin2)
        self._steer_motor = gpio.Motor(steer_pin1,steer_pin2) 

        self._control_dict = {"forward":self._drive_motor.forward,
                              "reverse":self._drive_motor.reverse,
                              "brake":self._drive_motor.brake,
                              "coast":self._drive_motor.coast,
                              "left":self._left,
                              "right":self._right,
                              "center":self._steer_center}
        
        self._current_steer_motor_state = 0

        self._left_return_constant =  left_return_constant
        self._right_return_constant = right_return_constant

    def _left(self,owner):
       
        with self._lock: self._current_steer_motor_state = -1
        self._steer_motor.forward(owner)

    def _right(self,owner):
        
        with self._lock: self._current_steer_motor_state = 1
        self._steer_motor.reverse(owner)

    def _steer_center(self,owner):

        # Steering wheels in the left-hand position
        if self._current_steer_motor_state == -1:

           self._steer_motor.reverse(owner)
           time.sleep(self._left_return_constant)
           self._steer_motor.coast(owner)

        # Steering wheels in the right-hand position
        if self._current_steer_motor_state == 1:
            
            self._steer_motor.forward(owner)
            time.sleep(self._left_return_constant)
            self._steer_motor.coast(owner)

        self._steer_motor.coast(owner)
        with self._lock: self._current_steer_motor_state = 0

    def shutdown(self,owner):
        
        self._steer_motor.coast(owner)
        self._drive_motor.coast(owner)

class TwoMotorCatSteer(RobotDevice):
    """
    Two gpio.Motor that work in synchrony as a cat drive.  The left and right
    motors go forward and reverse independently.  Steering is achieved by 
    running one forward, the other in reverse.  
    """ 
 
    def __init__(self,left_pin1,left_pin2,right_pin1,right_pin2,
                 pwm_frequency=100,pwm_duty_cycle=100,name=None,speed=0,
                 max_speed=5):
        """
        Initialize the motors.
    
        pins are GPIO pins.
        pwm_frequency and pwm_duty_cycle control pulse width modulation for the
            motors.  pwm_duty_cyle is used too control motor speed.
        speed: initial motor speed
        max_speed: maximum speed

        control_dict:
        forward: motors going forward, no kwargs
        reverse: motors going in reverse, no kwargs
        brake: use the motors as brakes, no kwargs
        coast: disengage the motors, no kwargs
        left: spin left, no kwargs
        right: spin right, no kwargs
        setspeed: set the motor speed, kwargs = {"speed":float}
        """

        RobotDevice.__init__(self,name)

        self._left_motor = gpio.Motor(left_pin1,left_pin2,pwm_frequency,pwm_duty_cycle)
        self._right_motor = gpio.Motor(right_pin1,right_pin2,pwm_frequency,pwm_duty_cycle) 
    
        self._control_dict = {"forward":self._forward,
                              "reverse":self._reverse,
                              "brake":self._brake,
                              "coast":self._coast,
                              "left":self._left,
                              "right":self._right,
                              "setspeed":self._set_speed}

        self._speed = speed
        self._max_speed = max_speed
        self._speed_constant = 100/max_speed

 
    def _forward(self,owner):

        self._left_motor.forward(owner)
        self._right_motor.forward(owner)

    def _reverse(self,owner):

        self._left_motor.reverse(owner)
        self._right_motor.reverse(owner)
        
    def _left(self,owner):
        
        self._left_motor.reverse(owner)
        self._right_motor.forward(owner)

    def _right(self,owner):
       
        self._left_motor.forward(owner) 
        self._right_motor.reverse(owner)
        
    def _brake(self,owner):

        self._left_motor.brake(owner)
        self._right_motor.brake(owner)
        
    def _coast(self,owner):

        self._left_motor.coast(owner)
        self._right_motor.coast(owner)

    def _set_speed(self,speed,owner):
        """
        Set the speed of the motors.
        """
    
        # Make sure the speed set makes sense. 
        if speed > self._max_speed or speed < 0:
            err = "speed {:.3f} is invalid".format(speed)

            self._append_message(RobotMessage(destination_device="warn",
                                              source_device=self.name,
                                              message=err))

            # Be conservative.  Since we recieved a mangled speed command, set
            # speed to 0.
            self._append_message(RobotMessage(destination="robot",
                                              destination_device=self.name,
                                              source="robot",
                                              source_device=self.name,
                                              message=["setspeed",{"speed":0}]))
        else:
            with self._lock: self._speed = speed

        self._left_motor.set_duty_cycle(self._speed*self._speed_constant,owner)
        self._right_motor.set_duty_cycle(self._speed*self._speed_constant,owner)
                     
    def shutdown(self,owner):

        self._left_motor.coast(owner)
        self._right_motor.coast(owner)


class IndicatorLight(RobotDevice):
    """
    Class for controlling an indicator light.
    """

    def __init__(self,control_pin,name=None,frequency=1,duty_cycle=100):
        """
        Initialize the light.

        control_pin is GPIO pin.  
        frequency and duty_cycle set pulse-width modulation parameters for LED.

        control_dict
        on: turn LED on, no kwargs
        off: turn LED off, no kwargs
        flip: flip state of LED, no kwargs
        flash: flash and LED, kwargs = {seconds_to_flash: float}
        """

        RobotDevice.__init__(self,name)

        self._led = gpio.LED(control_pin,frequency=frequency,duty_cycle=duty_cycle)

        self._control_dict = {"on":self._led.on,
                              "off":self._led.off,
                              "flip":self._led.flip,
                              "flash":self._flashLED}

    def _flashLED(self,owner,seconds_to_flash=5):
        """
        """

        self._led.on(owner)

        # Allows the client to turn on the LED for a fixed number of
        # seconds by adding a "turn off" message to the output queue.  This is
        # basically a "note to self: turn off the LED after delay time seconds"
        self._append_message(RobotMessage(destination="robot",
                                          destination_device=self.name,
                                          source="robot",
                                          source_device=self.name,
                                          delay_time=seconds_to_flash*1000,
                                          message="off"))
       
 
    def shutdown(self,owner):

        self._led.off(owner)


class RangeFinder(RobotDevice):
    """
    Class wrapping a GPIO range finder.
    """

    def __init__(self,trigger_pin,echo_pin,name=None,timeout=5000):
        """
        Initialize ranging system.

        trigger_pin and echo_pin set GPIO pins.

        control_dict:
        get: get the range, no kwargs
        """

        RobotDevice.__init__(self,name)

        self._range_finder = gpio.UltrasonicRange(trigger_pin,echo_pin,timeout)
        self._control_dict = {"get":self._get_range}
        self._range_value = -10.0
        self._messages = []

    def _get_range(self,owner):
        """
        Measure the range.
        """

        self._range_value = self._range_finder.getRange(owner)

        if (self._range_value < 0):
            self._append_message(RobotMessage(destination_device="warn",
                                              source_device=self.name,
                                              message="range finder timed out"))
        else:
            self._append_message(RobotMessage(source_device=self.name,
                                              message="{:.12f}".format(self._range_value)))

    def get_now(self,owner):
        """
        Return current range -- don't bother with that asynchronous stuff.
        """

        return self._range_finder.getRange()

