__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

import multiprocessing, time, random, copy

from rpyBot.messages import RobotMessage

class DeviceManager:
    """
    Class for aynchronous communication and integration between all of the 
    devices attached to the robot.  It runs on the main thread and then spawns
    a thread for each device attached to the robot.
    """
 
    def __init__(self,device_list=[],poll_interval=0.1,verbosity=0):
        """
        Initialize.  
            device_list: list of RobotDevice instances
            poll_interval: how often to poll messaging queues (in seconds) 
            verbosity: whether or not to spew messages to standard out 
        """
    
        self.device_list = device_list
        self.poll_interval = poll_interval
        self.verbosity = verbosity
        self.queue = [] 

        self.loaded_devices = []
        self.loaded_devices_dict = {}
        self.device_processes = []

        self.manager_id = int(random.random()*1e9)

        self._run_loop = False

    def start(self):
        """
        Start the main loop running.
        """      
 
        self._run_loop = True 
        self._run()

    def stop(self):
        """
        Stop the main loop from running.  Does not automatically unload devices
        or stop them.
        """
        
        self._run_loop = False

    def shutdown(self):
        """
        Shutdown all loaded devices (will propagate all the way down to cleanup
        of GPIO pins).  
        """

        for d in self.loaded_devices:
            self.unload_device(d.name)

    def load_device(self,d):
        """
        Load a device into the DeviceManager.
        """

        try:
            d.connect(self.manager_id)
            if d.name in list(self.loaded_devices_dict.keys()):
                message = "device {:s} already connected!".format(d.name)
                self._queue_message(message,destination_device="warn")
            else:
                self.loaded_devices.append(d)
                self.loaded_devices_dict[d.name] = len(self.loaded_devices) - 1
                self.device_processes.append(multiprocessing.Process(target=self.loaded_devices[-1].start))
                self.device_processes[-1].start()

        except exceptions.BotConnectionError as err:
            self._queue_message(err,destination_device="warn")
        
    def unload_device(self,device_name):
        """
        Unload a device from the control of the DeviceManager.
        """

        try:       
            index = self.loaded_devices_dict[device_name] 

            # Stop the device, diconnect it from this device manager instance, 
            # and then kill its thread.        
            self.loaded_devices[index].stop(self.manager_id)
            self.loaded_devices[index].disconnect()
            self.device_processes[index].terminate()
  
            # Remove it from the lists holding the devices.  
            for k in self.loaded_devices_dict.keys():
                self.loaded_devices_dict[k] -= 1

            self.loaded_devices.pop(index)
            self.loaded_devices_dict.pop(device_name)
            self.loaded_devices_processes.pop(index)

        except KeyError:
            message = "device {} is not connected".format(device_name)
            self._queue_message(message,destination_device="warn")

       
    def _run(self):

        for d in self.device_list:
            self.load_device(d)
   
        self._queue_message("starting system") 

        while self._run_loop:

            # Go through the queue and pipe messages to appropriate devices
            if len(self.queue) > 0:

                # Get the next message
                message = self._get_message()
 
                # If the message is past its delay, send it to a device.  If not, 
                # stick it back into the queue 
                if message.check_delay() == True:
                    self._message_to_device(message)
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

    def _message_to_device(self,message):
        """ 
        Send a RobotMessage instance to appropriate devices 
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
        """
        Return the first message in the queue.
        """ 

        if len(self.queue) == 0:
            return

        message = self.queue.pop(0) #.get()

        # If this is a raw message string, convert it to a RobotMessage
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
