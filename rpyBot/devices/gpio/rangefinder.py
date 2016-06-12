
import time

from . import hardware, GPIORobotDevice

class RangeFinder(GPIORobotDevice):
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

        GPIORobotDevice.__init__(self,name)

        self._range_finder = hardware.UltrasonicRange(trigger_pin,echo_pin,timeout)
        self._control_dict = {"get":self._get_range}
        self._range_value = -10.0

    def _get_range(self,owner):
        """
        Measure the range.
        """

        self._range_value = self._range_finder.get_range(owner)

        if (self._range_value < 0):
            self._queue_message("range finder timed out",destination_device="warn")
        else:
            self._queue_message("{:.12f}".format(self._range_value))

    def shutdown(self,owner):
        """
        Shutdown the gpio pins associated with this device.
        """

        self._range_finder.shutdown(owner)
