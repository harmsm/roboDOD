__description__ = \
"""
Classe for holding messages to pass back and forth in asyncrhonous
fashion.
"""
__author__ = "Michael J. Harms"
__date__ = "2014-12-29"

import time

class RobotMessage:
    """
    Class for handling timestamped messages and converting between the string
    messages that need to be sent over the web socket.
    """

    def __init__(self,destination="controller",destination_device="",
                      source="robot",source_device="",
                      delay_time=0,message=""):

        # arrival time (in ms)
        self.arrival_time = time.time()*1000

        self.destination = destination
        self.destination_device = destination_device
        self.source = source
        self.source_device = source_device
        self.delay_time = delay_time
        self.message = message

        self.minimum_time = self.arrival_time + self.delay_time

    def fromString(self,message_string):
        """
        Parse a message string and use it to populate the message.
        """

        message_array = message_string.split("|")

        try:

            dest = message_array[0]
            self.destination = dest.split(".")[0]
            self.destination_device = dest.split(".")[1]

            src = message_array[1]
            self.source = src.split(".")[0] 
            self.source_device = src.split(".")[1] 

            self.delay_time = float(message_array[2])
            self.message = "|".join(message_array[3:])

        except:
            err = "mangled message ({:s}) recieved!".format(message_string)
            return RobotMessage(destination_device="warn", message=err)


        self.minimum_time = self.arrival_time + self.delay_time

    def asString(self):
        """
        Convert a message instance to a string.
        """
        out = "{:s}.{:s}|{:s}.{:s}|{:.3f}|{:s}".format(self.destination,
                                                       self.destination_device,
                                                       self.source,
                                                       self.source_device,
                                                       self.delay_time,
                                                       self.message)

        return out

    def checkDelay(self):
        """
        See if a message is ready to send given its time stamp.
        """

        if time.time() > self.minimum_time:
            return True

        return False
     
