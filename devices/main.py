__description__ = \
"""
These classes, built on the base-class RobotDevice, are used to provide the
hardware-specific functions required for each device.  Each class has six 
public methods:

connectManager: put device under exclusive control of a DeviceManager instance
disconnectManager: drop current controlling DeviceManager instance
get: get any messages since last polled, clearing messages
put: send a command to the device (via private methods in _control_dict)
get_now: return data from device directly, skipping asynchrony
shutdown: safely shutdown the hardware

All other methods should private and controlled via the put() method. put takes
a command of the form:

    "key" OR
    ["key",{kwarg1:value1,kwarg2:value2...}"]

When writing methods, all functions should access self._messages via the 
self._append_message and self._get_messages methods, as these use a re-enterant
thread lock to stay thread-safe.  This is critical because the tornado server
and device manager are on different threads but can both post messages.
""" 
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

from random import random
import time, threading
from messages import RobotMessage


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
            self.name = "{:s}{.3f}".format(self.__class__.__name__,time.time())

        self._control_dict = {}
        self._manager = None

        self._lock = threading.RLock()
        self._messages = []

    def connectManager(self,manager):
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
 
    def disconnectManager(self):
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
    

    def put(self,command,owner):
        """
        Send a commmand to the device.  Expects to have structure:

            message = "key_for_control_dict~{kwarg1:value1,kward2:value2...}"

        and is parsed like:

            self._control_dict[key_for_control_dict](**kwargs)
        """

        try:

            # kwargs are specified, parse!
            if type(command) == list:
                try:
                    function_key = command[0]
                    kwargs = command[1]
                    self._control_dict[function_key](owner=owner,**kwargs)
                except:
                    err = "Mangled command ({:s})".format(command)
                    self._append_message(RobotMessage(destination_device="warn",
                                                      source_device=self.name,
                                                      message=err))

            # No kwargs specified         
            else:
                self._control_dict[command](owner=owner)

            # Send the message we just processed back to the controller.
            self._append_message(RobotMessage(source_device=self.name,
                                              message=command))


        # ownership collision, try again on next pass
        except OwnershipError:
            self._append_message(RobotMessage(destination="robot",
                                              destination_device=self.name,
                                              message=command))

        # Problem somewhere.
        except:
            err = "Command {:s} failed for {:s}. Trying again.".format(command,
                                                                       self.__class__.__name__)
            self._append_message(RobotMessage(destination_device="warn",
                                              source_device=self.name,
                                              message=err))
 
    def get_now(self,command,owner):
        """
        Return value immediately; forget that asynchronous stuff.
        """
        
        return None
 
    def shutdown(self,owner):
        """
        Safely shut down the piece of hardware.  
        """

        pass

    def _append_message(self,msg):
        """
        Append to self._messages in a thread-safe manner.
        """

        with self._lock:
            self._messages.append(msg)

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

class DummyDevice(RobotDevice):
    """
    This is a virtual device for dealing with general messages that apply to 
    all devices, etc.
    """

    def __init__(self,name=None):

        RobotDevice.__init__(self,name)

    def put(self,command):
        """
        This dummy function basically echoes the command back to the 
        device manager.
        """

        self._append_message(RobotMessage(source_device=self.name,
                                          message=command))

