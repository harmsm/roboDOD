
import gpio
from . import RobotDevice
from messages import RobotMessage

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

        self._motor.shutdown(owner)


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
        
        self._steer_motor.shutdown(owner)
        self._drive_motor.shutdown(owner)

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

        self._left_motor.shutdown(owner)
        self._right_motor.shutdown(owner)
        

