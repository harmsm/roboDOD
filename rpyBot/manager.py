__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

import multiprocessing, time, random
from copy import copy

from rpyBot.messages import RobotMessage

class DeviceManager(multiprocessing.Process):
    """
    Class for aynchronous communication and integration between all of the 
    devices attached to the robot.  Inherits from a multiprocessing.Process
    class, meaning that communication etc. can be polled via the input_queue
    and output_queues. 
    """
 
    def __init__(self,device_list=[],poll_interval=0.1,verbosity=0):
        """
        Initialize.  

            device_list: list of RobotDevice instances
            poll_interval: how often to poll messaging queues (in seconds)     
        """
    
        multiprocessing.Process.__init__(self)

        self.device_list = device_list
        self.poll_interval = poll_interval
        self.verbosity = verbosity

        self.input_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()
        self.loaded_devices = []
        self.loaded_devices_dict = {}

        for d in device_list:
            self.load_device(d)

        self.manager_id = int(random.random()*1e9)
 
    def load_device(self,d):
        """
        Load a device into the DeviceManager.
        """

        # load the device. d.connect_manager will return None unless there is
        # a problem.        
        status = d.connect_manager(self.__class__.__name__)
        if status != None:
            err = RobotMessage(destination_device="warn",
                               message=status)
            self.output_queue.put(err)
        else:
            self.loaded_devices.append(d)
            if d.name in list(self.loaded_devices_dict.keys()):
                err = RobotMessage(destination_device="warn",
                                   message="device {:s} already connected!".format(d.name))
                self.output_queue.put(err)
            else:
                self.loaded_devices_dict[d.name] = len(self.loaded_devices) - 1
       
    def unload_device(self,device_name):
        """
        Unload a device from the control of the DeviceManager.
        """

        try:       
            index = self.loaded_devices_dict[device_name] 
        except KeyError:
            err = RobotMessage(destination_device="warn",
                               message="device {:s} is not connected".format(device_name))
            self.output_queue.put(err)

        self.loaded_devices[index].disconnect_manager()
        self.loaded_devices.pop(index)
        self.loaded_devices_dict.pop(device_name)


    def message_to_device(self,message):
        """ 
        Send data to appropriate device in self.loaded_devices.
        """

        # If there is no destination device specified, send it out to the
        # output queue.  This basically just sends it to the user interface
        if message.destination_device == "":
            self.output_queue.put(message)

        try:
            self.loaded_devices[self.loaded_devices_dict[message.destination_device]].put(message)
        except KeyError:
            err = "device {:s} not loaded.".format(message.destination_device)
            self.output_queue.put(RobotMessage(destination_device="warn",message=err))
       
    def close(self):
        """
        When the DeviceManager instance is killed, release all of the devices so
        they can be picked up by another device manager.
        """

        for d in self.loaded_devices:
            d.disconnect_manager()

    def shutdown(self):
        """
        Shutdown all loaded devices (will propagate all the way down to cleanup
        of GPIO pins).  
        """

        for d in self.loaded_devices:
            d.shutdown(self.manager_id)

    def run(self):

        while True: 

            # Look for incoming user interface request(s) and pipe them to
            # appropriate device
            if not self.input_queue.empty():

                message = self.input_queue.get()
    
                # If this is a raw message string, convert it to an InternalMessage
                # instance 
                if type(message) == str:

                    m = RobotMessage()

                    # from_string only returns something if the input message was
                    # mangled.  If it's mangled, put the output -- which is a 
                    # RobotMessage instance warning of the mangling -- back into
                    # the queue.
                    status = m.from_string(message)
                    if status != None:
                        self.output_queue.put(status)
                        continue

                    message = copy(m)

                if self.verbosity > 0:
                    print(message.as_string())
 
                # If the message is past its delay, send it to a device.  If not, 
                # stick it back into the queue 
                if message.check_delay() == True:
                    self.message_to_device(message)
                else:
                    self.input_queue.put(message)
                
            # Rotate through the loaded devices and see if any of them have  
            # output ready.  Route this output to the appropriate queue. 
            for d in self.loaded_devices:

                device_output = d.get()

                for o in device_output:

                    if o.destination == "robot":
                        self.input_queue.put(o)
                    else:
                        self.output_queue.put(o)

                    if self.verbosity > 0:
                        print(o.as_string())

            # Wait poll_interval seconds before checking queues again
            time.sleep(self.poll_interval)

