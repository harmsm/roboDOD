__description__ = \
"""
These classes, built on the base-class RobotDevice, are used to
provide the hardware-specific functions required for each device.  The
manager software expects all pieces of hardware to have five public 
methods: connectManager, which allows the manager to declare to any
competing managers that it is in charge of this device; 
disconnectManager, obviously the inverse of connectManager; getData,
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
# XXX
#from lowLevel import *
import time, multiprocessing
import numpy as np

class RobotDeviceError(Exception):
    """
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
            self.name = "%s%i" % (self.__class__.__name__,int(random()*100000))

        self.control_dict = {}
        self.manager = None

    def connectManager(self,manager):
        """
        Connect this device to requesting manager, unless we're already connected
        elsewhere.
        """

        if self.manager != None:
            err = "%s already under control of %s.\n" % (self.name,
                                                         self.manager)
            raise RobotDeviceError(err)
        else:       
            self.manager = manager
    
    def disconnectManager(self):
        """
        Drop the connection to the manager.
        """      
 
        self.manager = None 

    def getData(self):
        """
        Function to poll this piece of hardware for new data to pass to the 
        manager.
        """

        return None

    def sendData(self,command):
        """
        Send a commmand to the device. 
        """
       
        try:
            self.control_dict[command]()
        except KeyError:
            err = "%s is not a recognized command for %s." % (command,
                                                              self.__class__.__name__)
            raise RobotDeviceError(err)
   
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
        self.has_a_message = False
        self.message = None

    def sendData(self,command):
        """
        This dummy function basically echoes the command back to the 
        device manager.
        """

        self.has_a_message = True
        self.message = command

    def getData(self):
        """
        """
    
        if self.has_a_message:
            self.has_a_message = False

            return "robot|info|robot recieved %s" % self.message

        return None
        

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
                             "coast":self.motor.coast}

    def shutDown(self):
        """
        Shut down the motor.
        """

        self.motor.coast()

class TwoMotorDriveSteer(RobotDevice):
    """
    Two GPIOMotors that work in synchrony.  The drive motor does forward and 
    reverse, the steer motor moves the wheels left and right.
    """ 
 
    def __init__(self,drive_pin1,drive_pin2,steer_pin1,steer_pin2,name=None):
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

        self.LEFT_RETURN_CONSTANT =  0.03
        self.RIGHT_RETURN_CONSTANT = 0.03

    def steerLeft(self):
        """
        """
        
        self.current_steer_motor_state = -1
        self.steer_motor.forward()

    def steerRight(self):
        """
        """
        
        self.current_steer_motor_state = 1
        self.steer_motor.reverse()

    def steerCenter(self):
        """
        """

        # Steering wheels in the left-hand position
        if self.current_steer_motor_state == -1:

           self.steer_motor.reverse()
           time.sleep(self.LEFT_RETURN_CONSTANT)
           self.steer_motor.coast()

        # Steering wheels in the right-hand position
        if self.current_steer_motor_state == 1:
            
            self.steer_motor.forward()
            time.sleep(self.LEFT_RETURN_CONSTANT)
            self.steer_motor.coast()

        self.steer_motor.coast()
        self.current_steer_motor_state = 0

    def shutDown(self):
        
        self.steer_motor.coast()
        self.drive_motor.coast()


class RangeFinder(RobotDevice):
    """
    Class wrapping a GPIO range finder.
    """

    def __init__(self,echo_pin,trigger_pin,name=None,timeout=5000):
        """
        Initialize ranging system.
        """

        RobotDevice.__init__(self,name)

        self.range_finder = gpio.UltrasonicRange(echo_pin,trigger_pin,timeout)
        self.control_dict = {"get":self.getRange}
        self.range_value = -1.0
        self.has_a_message = False

    def getRange(self):
        """
        Calculate the range.
        """

        self.has_a_message = True
        
        self.range_value = self.range_finder.getRange()

    def getData(self):
        """
        If a distance was calculated since we last checked, return it.
        """

        if self.has_a_message:
            self.has_a_message = False

            return "robot|%s|%.12f" % (self.name,self.range_value)

        return None

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


        self.has_a_message = False
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
        self.has_a_message = True

    def getData(self):
        """
        Return accelerometer data if it has been calculated.
        """

        # The device has a message!
        if self.has_a_message:
            self.has_a_message = False

            return "%.10e," % (self.state_vector)

        return None

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
        
