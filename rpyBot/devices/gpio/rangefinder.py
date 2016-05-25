
import time

from . import gpio
from devices import RobotDevice
from messages import RobotMessage

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

        self._range_value = self._range_finder.get_range(owner)

        if (self._range_value < 0):
            self._append_message(RobotMessage(destination_device="warn",
                                              source_device=self.name,
                                              message="range finder timed out"))
        else:
            self._append_message(RobotMessage(source_device=self.name,
                                              message="{:.12f}".format(self._range_value)))

    def shutdown(self,owner):
        """
        Shutdown the gpio pins associated with this device.
        """

        self._range_finder.shutdown(owner)
