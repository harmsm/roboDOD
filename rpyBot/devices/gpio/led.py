
from . import hardware, GPIORobotDevice

class IndicatorLight(GPIORobotDevice):
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

        GPIORobotDevice.__init__(self,name)

        self._led = hardware.LED(control_pin,frequency=frequency,duty_cycle=duty_cycle)

        self._control_dict = {"on":self._led.on,
                              "off":self._led.off,
                              "flip":self._led.flip,
                              "flash":self._flash_led,
                              "duty":self._led.set_duty_cycle,
                              "freq":self._led.set_frequency}

    def _flash_led(self,owner,seconds_to_flash=5):
        """
        """

        self._led.on(owner)

        # Allows the client to turn on the LED for a fixed number of
        # seconds by adding a "turn off" message to the output queue.  This is
        # basically a "note to self: turn off the LED after delay time seconds"
        self._queue_message("off",
                            destination="robot",
                            destination_device=self.name,
                            delay_time=seconds_to_flash*1000)
       
 
    def stop(self,owner):

        self._led.stop(owner)


class LightTower(GPIORobotDevice):
    """
    Control a linear array of LEDs, either independently or as a group.
    """

    def __init__(self,control_pins,name=None,frequency=1,duty_cycle=100):
        """
        Initialize the light.

        control_pins is a list-like object of GPIO pins.
        frequency and duty_cycle set pulse-width modulation parameters for LEDs.

        control_dict
        on: turn LED on, no kwargs
        off: turn LED off, no kwargs
        flip: flip state of LED, no kwargs
        flash: flash and LED, kwargs = {seconds_to_flash: float}
        roll: roll through the LEDs sequentially until stopped. 
              kwargs = {roll_time: float <- seconds between roll,
                        starting_led: int <- first led (list index, not pin)}
        stoproll: stop an existing led roll
        duty: set duty cycle, kwargs = {duty_cycle: float}
        freq: set frequency, kwargs = {frequency: float}
        """

        GPIORobotDevice.__init__(self,name)

        self._led_list = []
        for i in control_pins:
            self._led_list.append(hardware.LED(i,frequency=frequency,
                                               duty_cycle=duty_cycle))

        control_dict = {"on":self._on,
                        "off":self._off,
                        "flip":self._flip,
                        "flash":self._flash,
                        "roll":self._roll,
                        "duty":self._duty,
                        "freq":self._freq}
    
    def _on(self,led_number=None,owner=None):
        """
        If the led_number is specified, turn on a specific led.  Otherwise,
        turn on all of them.
        """

        if led_number is not None:
            self._led_list[led_number].on(owner)
        else:
            for l in self._led_list:
                l.on(owner)

    def _off(self,led_number=None,owner=None):
        """
        If the led_number is specified, turn off a specific led.  Otherwise,
        turn off all of them.
        """

        if led_number is not None:
            self._led_list[led_number].off(owner)
        else:
            for l in self._led_list:
                l.off(owner)

    def _flip(self,led_number=None,owner=None):
        """
        If the led_number is specified, flip state of a specific led.  Otherwise,
        flip all of them.
        """

        if led_number is not None:
            self._led_list[led_number].flip(owner)
        else:
            for l in self._led_list:
                l.flip(owner)

    def _duty(self,led_number=None,duty_cycle=100.0,owner=None):
        """
        If the led_number is specified, set duty cycle of a specific led.  Otherwise,
        set duty on all of them.
        """

        if led_number is not None:
            self._led_list[led_number].set_duty_cycle(duty_cycle,owner)
        else:
            for l in self._led_list:
                l.set_duty_cycle(duty_cycle,owner)

    def _freq(self,led_number=None,frequency=1,owner=None):
        """
        If the led_number is specified, set frequency of a specific led.  Otherwise,
        set frequency on all of them.
        """

        if led_number is not None:
            self._led_list[led_number].set_frequency(frequency,owner)
        else:
            for l in self._led_list:
                l.set_frequency(frequency,owner)


    def _flash(self,led_number=None,seconds_to_flash=5,owner=None):
        """
        Flash an LED by turning it on, then appending a message that says to turn
        it off after seconds_to_flash seconds. 
        """

        if led_number is not None:
            self._led_list[led_number].on(owner)
            self._queue_message(["off",{"led_number":led_number}],
                                destination_device=self.name,
                                delay_time=seconds_to_flash*1000)
        else:
            for l in self._led_list:
                l.on(owner)

            self._queue_message("off",destination_device=self.name,
                                delay_time=seconds_to_flash*1000)

    def _roll(self,roll_time=1.0,starting_led=0,owner=None):
        """
        Turn on LEDs sequentially in rolling fashion until interrupted by
        self._stop_roll.

            roll_time: time in seconds between moving to next led
            starting_led: led on which to start the roll.
            owner: owner of leds while being set.
        """
       
        # Flip all leds off. 
        self._off(owner=owner)

        # Check to see if _stop_roll has been called, which will set 
        # self._rolling_status to "Stop running" and thus break the 
        # _roll loop. If this is the first time ._roll has been called, this
        # will thrown an attribute error -- so initialize the attribute.
        try:
            if self._rolling_status == "Not running":
                self._rolling_status = "Running"
            elif self._rolling_status == "Stop running":
                self._rolling_status = "Not running"
                return 
            else:
                self._rolling_status = "Running"
        except AttributeError:
            self._rolling_status = "Running"

        # Now, turn on the starting led
        self._led_list[starting_led].on(owner)
      
        # Determine the next led we will turn on. 
        starting_led += starting_led 
        if starting_led >= len(self._led_list):
            starting_led -= len(self._led_list)

        # Now queue a message to turn on the next led after roll_time has elapsed.
        self._queue_message(["roll",{"starting_led":starting_led,
                                     "roll_time":roll_time}],
                            destination_device=self.name,
                            delay_time=roll_time*1000)

    def _stop_roll(self,owner):
        """
        Interrupt the rolling LEDs.
        """

        self._rolling_status = "Stop running"

