__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

import multiprocessing, time, random, copy

from rpyBot.messages import RobotMessage

class DeviceManager: #(multiprocessing.Process):
    """
    Class for aynchronous communication and integration between all of the 
    devices attached to the robot.  It uses a multiprocessing.Queue instance
    to poll for messages. 
    """
 
    def __init__(self,device_list=[],poll_interval=0.1,verbosity=0):
        """
        Initialize.  
            device_list: list of RobotDevice instances
            poll_interval: how often to poll messaging queues (in seconds) 
            verbosity: whether or not to spew messages to standard out 
        """
    
        #multiprocessing.Process.__init__(self)

        self.device_list = device_list
        self.poll_interval = poll_interval
        self.verbosity = verbosity
        self.queue = [] #multiprocessing.Queue()

        self.loaded_devices = []
        self.loaded_devices_dict = {}
        self.device_processes = []

        self.manager_id = int(random.random()*1e9)

    def start(self):
        
        multiprocessing.Process.start(self)


    def load_device(self,d):
        """
        Load a device into the DeviceManager.
        """

        # load the device. d.connect_manager will return None unless there is
        # a problem.        
        status = d.connect_manager(self.__class__.__name__)
        if status != None:
            self._queue_message(status,destination_device="warn")
        else:
            self.loaded_devices.append(d)
            if d.name in list(self.loaded_devices_dict.keys()):
                message = "device {:s} already connected!".format(d.name)
                self._queue_message(message,destination_device="warn")
            else:
                self.loaded_devices_dict[d.name] = len(self.loaded_devices) - 1

                self.device_processes.append(multiprocessing.Process(target=self.loaded_devices[-1].start))
                self.device_processes[-1].start()
           
    def unload_device(self,device_name):
        """
        Unload a device from the control of the DeviceManager.
        """

        try:       
            index = self.loaded_devices_dict[device_name] 
        except KeyError:
            message = "device {:s} is not connected".format(device_name)
            self._queue_message(message,destination_device="warn")

        self.loaded_devices[index].stop()
        self.loaded_devices[index].disconnect_manager()
        self.loaded_devices.pop(index)
        self.loaded_devices_dict.pop(device_name)

    def message_to_device(self,message):
        """ 
        Send data to appropriate device in self.loaded_devices.
        """

        # if the message is sent to the virtual "warn" device, forward this to
        # the controller
        if message.destination_device == "warn":
            self.loaded_devices[self.loaded_devices_dict["controller"]].put(message)
            return

        try:
            self.loaded_devices[self.loaded_devices_dict[message.destination_device]].put(message)
        except KeyError:
            err = "device \"{}\" not loaded.".format(message.destination_device)
            self._queue_message(err,destination_device="warn")
       
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

        for d in self.device_list:
            self.load_device(d)
   
        self._queue_message("starting system") 

        while True: 

            # Go through the queue and pipe messages to appropriate devices
            if not len(self.queue) > 0: #.empty():

                # Get the next message
                message = self._get_message()
 
                # If the message is past its delay, send it to a device.  If not, 
                # stick it back into the queue 
                if message.check_delay() == True:
                    self.message_to_device(message)
                else:
                    self._queue_message(message)
            
            # Rotate through the loaded devices and see if any of them have  
            # output ready.  If so, put the output into the queue for the next
            # pass.
            for d in self.loaded_devices:
                msgs = d.get()
                for m in msgs:   
                    self._queue_message(m)

            # Wait poll_interval seconds before checking queues again
            time.sleep(self.poll_interval)

    def _queue_message(self,
                       message="",
                       destination="robot",
                       destination_device="",
                       delay_time=0.0,
                       msg_string=None):
        """
        Append to a RobotMessage instance to to the message queue.  If message
        is already a RobotMessage, pass it through without modification.  If it
        is a string, construct the RobotMessage, setting source to "manager".
        """

        if type(message) != RobotMessage:

            m = RobotMessage(destination=destination,
                             destination_device=destination_device,
                             source="manager",
                             source_device="",
                             delay_time=delay_time,
                             message=message)

            # If msg_string is set to something besides None, parse that string
            # and load into the RobotMessage instance.
            if msg_string != None:
                m.from_string(msg_string)

            message = m

        if self.verbosity > 0:
            message.pretty_print()      
                     
        self.queue.append(message) #.put(message)

    def _get_message(self):
 
        if len(self.queue) == 0:
            return

        message = self.queue.pop(0) #.get()

        # If this is a raw message string, convert it to an RobotMessage
        # instance 
        if type(message) == str:

            try:
                m = RobotMessage()
                m.from_string(message)
                message = m
            except exceptions.BotMessageError as err:
                message = "Mangled message ({})".format(err.args[0])
                self._queue_message(message,destination_device="warn")
                return None

        if self.verbosity > 0:
            message.pretty_print()

        return message
