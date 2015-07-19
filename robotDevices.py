__description__ = \
"""
These classes, built on the base-class RobotDevice, are used to provide the
hardware-specific functions required for each device.  Each class has six 
public methods:

connectManager: put device under exclusive control of a DeviceManager instance
disconnectManager: drop current controlling DeviceManager instance
get: get any messages since last polled, clearing messages
put: send a command to the device (via private methods in _control_dict)
getNow: return data from device directly, skipping asynchrony
shutdown: safely shutdown the hardware

All other methods should private and controlled via the put() method. put takes
a string command of the form:

    "key~{kwarg1:value1,kwarg2:value2...}"

parses it and sends it to _control_dict:

    self._control_dict[key](**kwargs)

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
    

    def put(self,command):
        """
        Send a commmand to the device.  Expects to have structure:

            message = "key_for_control_dict~{kwarg1:value1,kward2:value2...}"

        and is parsed like:

            self._control_dict[key_for_control_dict](**kwargs)
        """

        command_array = command.split("~")
        function_key = command_array[0]

        try:

            # kwargs are specified, parse!
            if len(command_array) > 1:
                try:
                    kwargs = eval(command_array[1])
                    self._control_dict[function_key](**kwargs)
                except:
                    err = "Mangled command ({:s})".format(command)
                    self._append_message(RobotMessage(destination_device="warn",
                                                      source_device=self.name,
                                                      message=err))

            # No kwargs specified         
            else:
                self._control_dict[function_key]()

            # Send the message we just processed back to the controller.
            self._append_message(RobotMessage(source_device=self.name,
                                              message=command))


        # Problem somewhere.
        except:
            err = "Command {:s} failed for {:s}. Trying again.".format(command,
                                                                       self.__class__.__name__)
            self._append_message(RobotMessage(destination_device="warn",
                                              source_device=self.name,
                                              message=err))
            self._append_message(RobotMessage(destination="robot",
                                              destination_device=self.name,
                                              message=command))
 
    def getNow(self,command):
        """
        Return value immediately; forget that asynchronous stuff.
        """
        
        return None
 
    def shutdown(self):
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

class GPIOMotor(RobotDevice):
    """
    Single GPIOMotor under control of two GPIO pins.
    """
 
    def __init__(self,pin1,pin2,name=None):
        """
        Initialize the motor, defining an allowable set of commands, as well as
        the gpio pins.  

        control_dict:
        forward: motor going forward, no kwargs
        reverse: motor going in reverse, no kwargs
        stop: stop the motor, no kwargs
        coast: disengage the motor, no kwargs
        set_dutycyle: set the PWM duty cycle, kwargs = {"duty_cycle":float}
        set_freq: set PWM frequency, kwargs = {"frequency":float}
        """

        RobotDevice.__init__(self,name)

        self._motor = gpio.GPIOMotor(pin1,pin2)
        self._control_dict = {"forward":self._motor.forward,
                              "reverse":self._motor.reverse,
                              "stop":self._motor.stop,
                              "coast":self._motor.coast,
                              "set_dutycycle":self._motor.setPWMDutyCycle,
                              "set_freq":self._motor.setPWMFrequency}

    def shutdown(self):
        """
        Shut down the motor.
        """

        self._motor.shutdown()


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
        stop: stop the drive motor, no kwargs
        coast: disengage the drive motor, no kwargs
        left: steer motor left, no kwargs
        right: steer motor right, no kwargs
        center: steer motor center, no kwargs
        """

        RobotDevice.__init__(self,name)

        self._drive_motor = gpio.GPIOMotor(drive_pin1,drive_pin2)
        self._steer_motor = gpio.GPIOMotor(steer_pin1,steer_pin2) 

        self._control_dict = {"forward":self._drive_motor.forward,
                              "reverse":self._drive_motor.reverse,
                              "stop":self._drive_motor.stop,
                              "coast":self._drive_motor.coast,
                              "left":self._steerLeft,
                              "right":self._steerRight,
                              "center":self.steerCenter}
        
        self._current_steer_motor_state = 0

        self._left_return_constant =  left_return_constant
        self._right_return_constant = right_return_constant

    def _steerLeft(self):
       
        with self._lock: self._current_steer_motor_state = -1
        self._steer_motor.forward()

    def _steerRight(self):
        
        with self._lock: self._current_steer_motor_state = 1
        self._steer_motor.reverse()

    def _steerCenter(self):

        # Steering wheels in the left-hand position
        if self._current_steer_motor_state == -1:

           self._steer_motor.reverse()
           time.sleep(self._left_return_constant)
           self._steer_motor.coast()

        # Steering wheels in the right-hand position
        if self._current_steer_motor_state == 1:
            
            self._steer_motor.forward()
            time.sleep(self._left_return_constant)
            self._steer_motor.coast()

        self._steer_motor.coast()
        with self._lock: self._current_steer_motor_state = 0

    def shutdown(self):
        
        self._steer_motor.shutdown()
        self._drive_motor.shutdown()

class TwoMotorCatSteer(RobotDevice):
    """
    Two GPIOMotors that work in synchrony as a cat drive.  The left and right
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
        stop: stop the motors, no kwargs
        coast: disengage the motors, no kwargs
        left: spin left, no kwargs
        right: spin right, no kwargs
        setspeed: set the motor speed, kwargs = {"speed":float}
        """

        RobotDevice.__init__(self,name)

        self._left_motor = gpio.GPIOMotor(left_pin1,left_pin2,pwm_frequency,pwm_duty_cycle)
        self._right_motor = gpio.GPIOMotor(right_pin1,right_pin2,pwm_frequency,pwm_duty_cycle) 
    
        self._control_dict = {"forward":self._driveForward,
                              "reverse":self._driveReverse,
                              "stop":self._motorStop,
                              "coast":self._motorCoast,
                              "left":self._steerLeft,
                              "right":self._steerRight,
                              "setspeed":self._setSpeed}

        self._speed = speed
        self._max_speed = max_speed
        self._speed_constant = 100/max_speed

 
    def _driveForward(self):

        self._left_motor.forward()
        self._right_motor.forward()

    def _driveReverse(self):

        self._left_motor.reverse()
        self._right_motor.reverse()
        
    def _steerLeft(self):
        
        self._left_motor.reverse()
        self._right_motor.forward()

    def _steerRight(self):
       
        self._left_motor.forward() 
        self._right_motor.reverse()
        
    def _motorStop(self):

        self._left_motor.stop()
        self._right_motor.stop()
        
    def _motorCoast(self):

        self._left_motor.coast()
        self._right_motor.coast()

    def _setSpeed(self,speed=0):
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
                                              message="setspeed~{\"speed\":0}"))
        else:
            with self._lock: self._speed = speed

        self._left_motor.setPWMDutyCycle(self._speed*self._speed_constant)
        self._right_motor.setPWMDutyCycle(self._speed*self._speed_constant)
                     
    def shutdown(self):

        self._left_motor.shutdown()
        self._right_motor.shutdown()


class LEDIndicatorLight(RobotDevice):
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

        self._led = gpio.GPIOLED(control_pin,frequency=frequency,duty_cycle=duty_cycle)

        self._control_dict = {"on":self._led.on,
                              "off":self._led.off,
                              "flip":self._led.flip,
                              "flash":self._flashLED}

    def _flashLED(self,seconds_to_flash=5):
        """
        """

        self._led.on()

        # Allows the client to turn on the LED for a fixed number of
        # seconds by adding a "turn off" message to the output queue.  This is
        # basically a "note to self: turn off the LED after delay time seconds"
        self._append_message(RobotMessage(destination="robot",
                                          destination_device=self.name,
                                          source="robot",
                                          source_device=self.name,
                                          delay_time=seconds_to_flash*1000,
                                          message="off"))
       
 
    def shutdown(self):

        self._led.off()


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
        self._control_dict = {"get":self._getRange}
        self._range_value = -10.0
        self._messages = []

    def _getRange(self):
        """
        Measure the range.
        """

        with self._lock: self._range_value = self._range_finder.getRange()
        if (self._range_value < 0):
            self._append_message(RobotMessage(destination_device="warn",
                                              source_device=self.name,
                                              message="range finder timed out"))
        else:
            self._append_message(RobotMessage(source_device=self.name,
                                              message="{:.12f}".format(self._range_value)))

    def getNow(self):
        """
        Return current range -- don't bother with that asynchronous stuff.
        """

        return self._range_finder.getRange()

