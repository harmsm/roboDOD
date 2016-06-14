__description__ = \
"""
The parent class RobotDevice.
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

from rpyBot import exceptions
from rpyBot.messages import RobotMessage
from random import random
import time, threading, copy

class RobotDevice:
    """
    Base class for connecting to low-level device functionality.  
    """

    def __init__(self,name=None):
        """
        Initialize the device.
        """

        # Give the devivce a unique name
        if name != None:
            self.name = name
        else:
            self.name = "{:s}{:.3f}".format(self.__class__.__name__,time.time())

        self._control_dict = {}
        self._manager = None

        self._lock = threading.RLock()
        self._messages = [] 

    @property
    def connected(self):
        
        if self._manager == None:
            return False
        return True


    def connect(self,manager):
        """
        Connect this device to requesting manager, unless we're already connected
        elsewhere.

        on error, return string.  Otherwise, return None.
        """

        if self.connected:
            err = "{:s} already under control of {:s}".format(self.name,
                                                              self._manager)
            raise exceptions.BotConnectionError(err)
        else:       
            self._manager = manager
   
    def disconnect(self):
        """
        Drop the connection to the manager.
        """      
 
        self._manager = None 

    def get(self):
        """
        Function to poll this piece of hardware for new messages to pass to the 
        manager.
        """

        return self._get_all_messages()
    

    def put(self,message):
        """
        The hardware is controlled in a thread-safe fashion by using the unique
        message.message_id integer to declare the owner of the hardware 
        associated with the device.
        """
   
        try:

            # kwargs are specified, parse!
            if type(message.message) == list:
                try:
                    function_key = message.message[0]
                    kwargs = message.message[1]
                    self._control_dict[function_key](owner=message.message_id,**kwargs)
                except:
                    err = "Mangled command ({:s})".format(message.message)
                    self._queue_message(err,destination_device="warn")

            # No kwargs specified         
            else:
                try:
                    self._control_dict[message.message](owner=message.message_id)
                except:
                    err = "Mangled command ({:s})".format(message.message)
                    self._queue_message(err,destination_device="warn")

            # Send the message we just processed back to the controller.
            self._queue_message(message.message)

        except:
            self._queue_message(message.message,destination_device="warn")
 
    def start(self):
        """
        Dummy function, in case device needs to be started up.
        """

        pass

    def stop(self,owner=None):
        """
        Dummy device.  Some devices need to be stopped.
        """
    
        pass


    def _queue_message(self,
                       message="",
                       destination_device="controller",
                       destination="",
                       delay_time=0.0,
                       msg_string=None):
        """
        Append to a RobotMessage instance to self._messages in a thread-safe
        manner.  Automatically set the source and source device.  Take args
        to set other attributes.
        """


        if type(message) != RobotMessage:

            m = RobotMessage(destination=destination,
                             destination_device=destination_device,
                             source="robot",
                             source_device=self.name,
                             delay_time=delay_time,
                             message=message)

            # If msg_string is set to something besides None, parse that string
            # and load into the RobotMessage instance.
            if msg_string != None:
                m.from_string(msg_string)
            message = m
                
        with self._lock:
            self._messages.append(message)             

    def _get_all_messages(self):
        """
        Get all self._messages (wiping out existing) in a thread-safe manner.
        """

        with self._lock:
            m = self._messages[:]
            self._messages = []

        return m

