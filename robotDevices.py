__description__ = \
"""
These classes, built on the base-class RobotDevice, are used to
provide the hardware-specific functions required for each device.  The
manager software expects all pieces of hardware to have five public 
methods: connectToManager, which allows the manager to declare to any
competing managers that it is in charge of this device; 
disconnectFromManager, obviously the inverse of connectToManager; getData,
which the manager uses to look for any messages the hardware may have
posted; sendData, which the manager uses to send commands to the hardware;
and shutDown, which is used to safely turn off the hardware.

Communication is all asynchronous at the moment.  A request for data is sent
via sendData, and then picked up the next time the manager polls via getData. 

To access data without the asynchronous stuff, use the getNow method.
""" 
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

from random import random
from lowLevel import *
from robotMessages import *
import time, multiprocessing
import numpy as np

class RobotDeviceError(Exception):
    """
    General error class for this module.
    """

    pass

class RobotDevice:
    """
    Base class for connecting to low-level device functionality.  
    """

    def __init__(self,name=None):

        # Give the devivce a unique name
        if name != None:
            self.name = name
        else:
            self.name = "%s%.3f" % (self.__class__.__name__,time.time())

        self.control_dict = {}
        self.manager = None

        self.messages = []

    def connectToManager(self,manager):
        """
        Connect this device to requesting manager, unless we're already connected
        elsewhere.
        """

        if self.manager != None:
            err = "%s already under control of %s.\n" % (self.name,
                                                         self.manager)
            raise RobotDeviceError("robot|-1|error|%s" % err)
        else:       
            self.manager = manager
    
    def disconnectFromManager(self):
        """
        Drop the connection to the manager.
        """      
 
        self.manager = None 

    def getData(self):
        """
        Function to poll this piece of hardware for new messages to pass to the 
        manager.
        """

        # If the list of messages is not empty
        if len(self.messages) > 0:
            m = self.messages[:]
            self.messages = []

            return m

        return []

    def sendData(message):
        """
        Send a commmand to the device. 
        """

        command = message.split("|")
       
        function_call = command[0]

        try:

            # kwargs are specified, parse!
            if len(command) > 1:
                try:
                    kwargs = eval(command[1])
                    self.control_dict[function_call](**kwargs)
                except (SyntaxError,TypeError):
                    err = "Mangled command arguments (%s)" % command[1]
                    raise RobotDeviceError(err)
            # No kwargs specified         
            else:
                self.control_dict[function_call]()

            # Send the message we just processed back to the controller.
            self.messages.append(RobotMessage(destination="controller",
                                              device_name=self.name,
                                              message=message))

        # command not recognized
        except KeyError:
            err = "Command (%s) not found for %s." % (command,self.__class__.__name__)
            raise RobotDeviceError("robot|-1|error|%s" % err)

            #self.messages.append(RobotMessage(destination="controller",
            #                                  device_name=self.name,
            #                                  message=message))
   
    def getNow(self,command):
        """
        Return value immediately; forget that asynchronous stuff.
        """
        
        return None
 
    def shutDown(self):
        """
        Safely shut down the piece of hardware.  
        """

        pass


class InfoDevice(RobotDevice):
    """
    This is a virtual device for dealing with general messages that apply to 
    all devices, etc.
    """

    def __init__(self,name=None):

        # Give the devivce a unique name
        if name != None:
            self.name = name
        else:
            self.name = "%s%i" % (self.__class__.__name__,int(random()*100000))

        self.control_dict = {}
        self.manager = None
        self.messages = []

    def sendData(self,command):
        """
        This dummy function basically echoes the command back to the 
        device manager.
        """

        self.messages.append(RobotMessage(destination="controller",
                                          self.name,
                                          message=command))

class GPIOMotor(RobotDevice):
    """
    Single GPIOMotor under control of two GPIO pins.
    """
 
    def __init__(self,pin1,pin2,name=None):
        """
        Initialize the motor, defining an allowable set of commands, as well as
        the gpio pins.  
        """

        RobotDevice.__init__(self,name)

        self.motor = gpio.GPIOMotor(pin1,pin2)
        self.control_dict = {"forward":self.motor.forward,
                             "reverse":self.motor.reverse,
                             "stop":self.motor.stop,
                             "coast":self.motor.coast,
                             "set_dutycycle":self.motor.setPWMDutyCycle,
                             "set_freq":self.motor.setPWMFrequency}

    def shutDown(self):
        """
        Shut down the motor.
        """

        self.motor.shutdown()


class TwoMotorDriveSteer(RobotDevice):
    """
    Two GPIOMotors that work in synchrony.  The drive motor does forward and 
    reverse, the steer motor moves the wheels left and right.
    """ 
 
    def __init__(self,drive_pin1,drive_pin2,steer_pin1,steer_pin2,name=None,
                 left_return_constant=0.03,right_return_constant=0.03):
        """
        Initialize the motors.
        """

        RobotDevice.__init__(self,name)

        self.drive_motor = gpio.GPIOMotor(drive_pin1,drive_pin2)
        self.steer_motor = gpio.GPIOMotor(steer_pin1,steer_pin2) 

        self.control_dict = {"forward":self.drive_motor.forward,
                             "reverse":self.drive_motor.reverse,
                             "stop":self.drive_motor.stop,
                             "coast":self.drive_motor.coast,
                             "left":self.steerLeft,
                             "right":self.steerRight,
                             "center":self.steerCenter}
        
        self.current_steer_motor_state = 0

        self.left_return_constant =  left_return_constant
        self.right_return_constant = right_return_constant

    def steerLeft(self):
        
        self.current_steer_motor_state = -1
        self.steer_motor.forward()

    def steerRight(self):
        
        self.current_steer_motor_state = 1
        self.steer_motor.reverse()

    def steerCenter(self):

        # Steering wheels in the left-hand position
        if self.current_steer_motor_state == -1:

           self.steer_motor.reverse()
           time.sleep(self.left_return_constant)
           self.steer_motor.coast()

        # Steering wheels in the right-hand position
        if self.current_steer_motor_state == 1:
            
            self.steer_motor.forward()
            time.sleep(self.left_return_constant)
            self.steer_motor.coast()

        self.steer_motor.coast()
        self.current_steer_motor_state = 0

    def shutDown(self):
        
        self.steer_motor.coast()
        self.drive_motor.coast()

class TwoMotorCatSteer(RobotDevice):
    """
    Two GPIOMotors that work in synchrony as a cat drive.  The left and right
    motors go forward and reverse independently.  Steering is achieved by 
    running one forward, the other in reverse.  
    """ 
 
    def __init__(self,left_pin1,left_pin2,right_pin1,right_pin2,
                 pwm_frequency=100,pwm_duty_cycle=100,name=None,speed=0):
        """
        Initialize the motors.
        """

        RobotDevice.__init__(self,name)

        self.left_motor = gpio.GPIOMotor(left_pin1,left_pin2,pwm_frequency,pwm_duty_cycle)
        self.right_motor = gpio.GPIOMotor(right_pin1,right_pin2,pwm_frequency,pwm_duty_cycle) 
    
        self.control_dict = {"forward":self.driveForward,
                             "reverse":self.driveReverse,
                             "stop":self.motorStop,
                             "coast":self.motorCoast,
                             "left":self.steerLeft,
                             "right":self.steerRight,
                             "setspeed":self.setSpeed}

        self.speed = speed       
 
    def driveForward(self):

        self.left_motor.forward()
        self.right_motor.forward()

    def driveReverse(self):

        self.left_motor.reverse()
        self.right_motor.reverse()
        
    def steerLeft(self):
        
        self.left_motor.reverse()
        self.right_motor.forward()

    def steerRight(self):
       
        self.left_motor.forward() 
        self.right_motor.reverse()
        
    def motorStop(self):

        self.left_motor.stop()
        self.right_motor.stop()
        
    def motorCoast(self):

        self.left_motor.coast()
        self.right_motor.coast()

    def shutDown(self):

        self.motorCoast()

    def setSpeed(self,speed=0):
        """
        Set the speed of the motor.
        """
       
        self.speed = speed
        self.left_motor.setPWMDutyCycle(speed*25)
        self.right_motor.setPWMDutyCycle(speed*25)
                     

class LEDIndicatorLight(RobotDevice):
    """
    Class for controlling an indicator light.
    """

    def __init__(self,control_pin,name=None,frequency=1,duty_cycle=100):
        """
        Initialize the light.
        """

        RobotDevice.__init__(self,name)

        self.led = gpio.GPIOLED(control_pin,frequency=frequency,duty_cycle=duty_cycle)

        self.control_dict = {"on":self.turnOn,
                             "off":self.turnOff,
                             "flip":self.led.flip,
                             "flash":self.flashLED}
                             #"setPWM":self.led.setPulseWidthModulation}

        # Take arguments for pwm from __init__ and pass them to set pwm


    def flashLED(self,seconds_to_flash=5):
        """
        """

        self.led.on()

        # Allows the client to turn on the LED for a fixed number of
        # seconds by adding a "turn off" message to the output queue.  This is
        # basically a "note to self: turn of the LED after delay time seconds"
        self.messages.append(RobotMessage(destination="robot",
                                          delay_time=seconds_to_flash,
                                          device_name=self.name,
                                          message="off"))
       
    def turnOn(self):
        """
        """

        self.led.on()
    
    def turnOff(self):
        """
        """

        self.led.off()
 
    def shutDown(self):
        """
        """

        self.led.off()


class RangeFinder(RobotDevice):
    """
    Class wrapping a GPIO range finder.
    """

    def __init__(self,trigger_pin,echo_pin,name=None,timeout=5000):
        """
        Initialize ranging system.
        """

        RobotDevice.__init__(self,name)

        self.range_finder = gpio.UltrasonicRange(trigger_pin,echo_pin,timeout)
        self.control_dict = {"get":self.getRange}
        self.range_value = -10.0
        self.messages = []

    def getRange(self):
        """
        Calculate the range.
        """

        self.range_value = self.range_finder.getRange()
        self.messages.append(RobotMessage(destination="controller",
                                          device_name=self.name,
                                          message="%.12f" % self.range_value))

    def getNow(self):
        """
        Return current range -- don't bother with that asynchronous stuff.
        """

        return self.range_finder.getRange()


class Accelerometer(RobotDevice):
    """
    """

    def __init__(self,port=1,name=None,calibrate=500,noise_cutoff=0.03,smooth_window=10):
        """
        """

        RobotDevice.__init__(self,name)
        
        self.accel = i2c.ADXL345Accelerometer(port)
        self.control_dict = {"get",self.getAccelData}


        # x, y, z, magnitude for acceleration
        #                        velocity
        #                        distance traveled
        self.state_vector = np.zeros(9,dtype=float)
        self.noise_cutoff = noise_cutoff
        self.smooth_window = smooth_window
        
        print("Calibrating accelerometer.")
        calibration_state_vector = np.zeros((calibrate,3),dtype=float)
        for i in range(calibrate):
            calibration_state_vector[i,] = self.accel.getAxes()

        self.offsets = np.array([0.,0.,0.]) - np.mean(calibration_state_vector,axis=0)

        print("Calibration complete.  Offsets are %r" % self.offsets)

        # Put acceleration into m/s
        self.scale = 9.8
            
        # Set up timers 
        self.previous_time = time.time()
        self.current_time = time.time() 


    def getAccelData(self):
        """
        """

        v = self.getNow()
        self.messages.append(RobotMessage(destination="controller",
                                          device_name=self.name,
                                          message="%.10e," % self.state_vector))


    def getNow(self):
        """
        Immediately return accelerometer state_vector.
        """

        self.previous_time = self.current_time

        all_accel = np.zeros((self.smooth_window,3),dtype=float)
        for i in range(self.smooth_window):
            all_accel[i,] = np.array(self.accel.getAxes()) 
        
        acceleration = np.mean(all_accel,axis=0) + self.offsets
        #simple noise filter
        #acceleration = acceleration*(np.abs(acceleration) > self.noise_cutoff)

        self.current_time = time.time()

        dt = self.current_time - self.previous_time

        velocity = dt*acceleration
        position = dt*velocity
        self.state_vector[0:3] = acceleration
        self.state_vector[3:6] += velocity
        self.state_vector[6:9] += position
         
        return self.state_vector
        
