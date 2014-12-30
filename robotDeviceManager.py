__description__ = \
"""
packet structure:
destination|time_delay|device_name|dict_key|[**kwargs]

"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

import multiprocessing, time
from robotMessages import *
from robotDevices import InfoDevice
from copy import copy

class RobotDeviceManagerError(Exception):
    """
    """

    pass


class DeviceManager(multiprocessing.Process):
    """
    """
 
    def __init__(self,input_queue,output_queue,device_list=[]):
        """
        """

        multiprocessing.Process.__init__(self)

        self.input_queue = input_queue
        self.output_queue = output_queue
        self.loaded_devices = []
        self.loaded_devices_dict = {}

        for d in device_list:
            self.loadDevice(d)

        # Load a virtual device for dealing with "info" commands
        self.loadDevice(InfoDevice(name="info"))
    
    def loadDevice(self,d):
        """
        Load a device into the DeviceManager.
        """
        
        d.connectToManager(self.__class__.__name__)
        self.loaded_devices.append(d)
        if d.name in list(self.loaded_devices_dict.keys()):
            err = "robot|-1|error|device %s already connected!\n" % d.name
            raise RobotDeviceManagerError(err)
        self.loaded_devices_dict[d.name] = len(self.loaded_devices) - 1
       
    def unloadDevice(self,device_name):
        """
        Unload a device from the control of the DeviceManager.
        """

        try:       
            index = self.loaded_devices_dict[device_name] 
        except KeyError:
            err = "robot|-1|error|device %s is not connected.\n" % device_name
            raise RobotDeviceManagerError(err)

        self.loaded_devices[index].disconnectFromManager()
        self.loaded_devices.pop(index)
        self.loaded_devices_dict.pop(device_name)

    def close(self):
        """
        When the DeviceManager instance is killed, release all of the devices so
        they can  be picked up by another device manager.
        """

        for d in self.loaded_devices:
            d.disconnectFromManager()

    def sendMessageToDevice(self,message):
        """ 
        Send data to appropriate device in self.loaded_devices.
        """

        try:

            try:
                self.loaded_devices[self.loaded_devices_dict[message.device_name]].sendData(message.message)
            except KeyError:
                err = "controller|-1|error|device %s not loaded.\n" % (message.device_name)
                raise RobotDeviceManagerError(err)
       
        except ValueError:
            err = "controller|-1|error|mangled packet (%s) recieved!\n" % (message.asString())
            raise RobotDeviceManagerError(err) 
 
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
                    m.loadMessageFromString(message)
                    message = copy(m)
             
                # If the message is past its delay, send it to a device.  If not, 
                # stick it back into the queue 
                if message.checkMessageTimestamp() == True:
                    self.sendMessageToDevice(message)
                else:
                    self.input_queue.put(message)
                
            # Rotate through the loaded devices and see if any of them have  
            # output ready.  Route this output to the appropriate queue. 
            for d in self.loaded_devices:

                device_output = d.getData()

                if device_output != None:

                    if device_output.destination == "robot":
                        self.input_queue.put(device_output)
                    else:
                        self.output_queue.put(device_output)


