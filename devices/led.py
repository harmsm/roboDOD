
from . import RobotDevice
from messages import RobotMessage

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
                              "flash":self._flash_led}

    def _flash_led(self,owner,seconds_to_flash=5):
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

        self._led.shutdown(owner)


