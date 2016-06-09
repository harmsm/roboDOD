__description__ = \
"""
The parent class RobotDevice.
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

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

    def connect_manager(self,manager):
        """
        Connect this device to requesting manager, unless we're already connected
        elsewhere.

        on error, return string.  Otherwise, return None.
        """

        if self._manager != None:
            err = "{:s} already under control of {:s}".format(self.name,
                                                              self._manager)
            return err
        else:       
            self._manager = manager
   
        return None
 
    def disconnect_manager(self):
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
        NEEDS TO BE UPDATED.  ACTUALLY ACCEPTS RobotMessage INSTANCE.
    
        Send a message to the device, using callbacks defined in _control_dict.
        message.message should either string key for the call back or a list 
        containing the string key and then a dict of kwargs.  i.e.:

            message.message = "a_callback_key"
        
        OR

            message.message = ["a_callback_key",{kwarg1:foo,kwarg2:bar...}]

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

        # Problem somewhere (THIS SENDS BACK TO THE DEVICE WITHOUT A DELAY!!!).
        except:
            self._queue_message(message.message,
                                destination="robot",
                                destination_device=self.name)
 
    def shutdown(self,owner):
        """
        Safely shut down the piece of hardware.  
        """

        pass

    def _queue_message(self,
                       message,
                       destination="controller",
                       destination_device="",
                       delay_time=0.0):
        """
        Append to a RobotMessage instance to self._messages in a thread-safe
        manner.  Automatically set the source and source device.  Take args
        to set other attributes.
        """

        with self._lock:

            m = RobotMessage(destination=destination,
                             destination_device=destination_device,
                             source="robot",
                             source_device=self.name,
                             delay_time=delay_time,
                             message=message)
                             
            self._messages.append(m)

    def _get_all_messages(self):
        """
        Get all self._messages (wiping out existing) in a thread-safe manner.
        """

        with self._lock:

            m = []
            if len(self._messages) > 0:
                m = self._messages[:]
                self._messages = []

            return m

