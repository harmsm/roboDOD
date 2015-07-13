__description__ = \
"""
Classes for holding messages to pass back and forth in asyncrhonous
fashion.
"""
__author__ = "Michael J. Harms"
__date__ = "2014-12-29"

import time

class RobotMessage:
    """
    Class for handling timestamped messages and converting between the string
    packets that need to be sent over the web socket.
    """

    def __init__(self,destination=None,source=None,delay_time=0,device_name=None,
                 message=""):

        self.arrival_time = time.time()

        self.destination = destination
        self.source = source
        self.delay_time = delay_time
        self.device_name = device_name
        self.message = message

        self.minimum_time = self.arrival_time + self.delay_time

    def loadMessageFromString(self,packet_string):
        """
        Parse a message string and use it to populate the message.
        """

        packet = packet_string.split("|")

        try:
            self.destination = packet[0]
            self.source = packet[1]
            self.delay_time = float(packet[2])
            self.device_name = packet[3]
            self.message = "|".join(packet[4:])
        except (IndexError,ValueError):
            err = "mangled packet ({:s}) recieved!".format(packet_string)
            raise RobotDeviceManagerError(err)

        self.minimum_time = self.arrival_time + self.delay_time

    def asString(self):
        """
        Convert a message instance to a string.
        """
        out = "{:s}|{:s}|{:.3f}|{:s}|{:s}".format(self.destination,
                                                  self.source,
                                                  self.delay_time,
                                                  self.device_name,
                                                  self.message)

        return out

    def checkMessageTimestamp(self):
        """
        See if a message is ready to send given its time stamp.
        """

        if time.time() > self.minimum_time:
            return True

        return False
     
