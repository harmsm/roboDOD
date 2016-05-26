__description__ = \
"""
Class for holding messages to pass back and forth in asynchronous
fashion.
"""
__author__ = "Michael J. Harms"
__date__ = "2014-12-29"

import time, json, random

class RobotMessage:
    """
    Class for handling timestamped messages and converting between the string
    messages that need to be sent over the web socket.
    """

    def __init__(self,destination="controller",
                      destination_device="",
                      source="robot",
                      source_device="",
                      delay_time=0.0,
                      message=""):

        # arrival time (in ms)
        self.arrival_time = int(time.time()*1000)

        self.destination = destination
        self.destination_device = destination_device
        self.source = source
        self.source_device = source_device
        self.delay_time = delay_time
        self.message_id = int(random.random()*1e9)
        self.message = message

        self.minimum_time = self.arrival_time + self.delay_time

    def from_string(self,message_string):
        """
        Parse a message string and use it to populate the message.
        """

        message_dict = json.loads(message_string)
        for k in message_dict.keys():
            self.__dict__[k] = message_dict[k]

        # Wipe out arrival time from message itself
        self.arrival_time = int(time.time()*1000)
        self.minimum_time = self.arrival_time + self.delay_time
        
    def as_string(self):
        """
        Convert a message instance to a string.
        """

        return json.dumps(self.__dict__)

    def check_delay(self):
        """
        See if a message is ready to send given its time stamp.
        """

        if int(1000*time.time()) > self.minimum_time:
            return True

        return False
     
