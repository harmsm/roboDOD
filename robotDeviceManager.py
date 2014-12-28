__description__ = \
"""
packet structure:
robot|device_name|dict_key|[**kwargs]

"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-18"

import multiprocessing, time
from robotDevices import InfoDevice
from robotSpatialAwareness import SpatialAwareness

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
            err = "robot|err|device %s already connected!\n" % d.name
            raise RobotDeviceManagerError(err)
        self.loaded_devices_dict[d.name] = len(self.loaded_devices) - 1
       
    def unloadDevice(self,device_name):
        """
        Unload a device from the control of the DeviceManager.
        """

        try:       
            index = self.loaded_devices_dict[device_name] 
        except KeyError:
            err = "robot|err|device %s is not connected.\n" % device_name
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

    def sendMessage(self,data):
        """ 
        Send data to appropriate device in self.loaded_devices.
        """

        packet = data.split("|")

        try:

            # Make sure the message was sent by us.  This deals with random spew
            # from the webserver etc.
            if packet[0] != "robot":
                return

            # Try to send the data to the device 
            try:
                self.loaded_devices[self.loaded_devices_dict[packet[1]]].sendData(packet[2:])
            except KeyError:
                err = "robot|error|device %s not loaded.\n" % (packet[1])
                raise RobotDeviceManagerError(err)
       
        except ValueError:
            err = "robot|error|mangled packet (%s) recieved!\n" % (data)
            raise RobotDeviceManagerError(err) 
 
    def run(self):

        while True:

            #XX <-- Send message, checking status.  If not complete -- say, 
            # waiting for timestamp -- append the message back to the queue

            # Look for incoming user interface request(s) and pipe them to
            # appropriate device
            if not self.input_queue.empty():
                user_input = self.input_queue.get()
                self.sendMessage(user_input)
                
            # Rotate through the loaded devices and see if any of them have  
            # output ready for user interface
            for d in self.loaded_devices:
                device_output = d.getData()

                if device_output != None:
                    self.output_queue.put(device_output)


