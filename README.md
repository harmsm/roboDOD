rpyBot
=======

software for controlling a robot via a raspberry pi

#Notes:

To use a device with i2c, you need to enable the I2C kernel modules and
then copy the quick2wire and i2clibraries into the roboDOD/lowLevel 
directory.  

    cd roboDOD/lowLevel
    git clone https://github.com/quick2wire/quick2wire-python-api.git
    git clone https://bitbucket.org/thinkbowl/i2clibraries.git

roboDOD will do the rest, in terms of setting environment variables etc.

##Messaging specification

Messages are passed in an asynchronous fashion with tornado input/output 
queues using the RobotMessage class (implemented in both js and python). This
class allows specification of `destination` and `destination_device`,
`source` and `source_device`, a `delay_time` for waiting to send a
message and the `message` itself.  On the robot side, the main instance of
the DeviceManager class routes each message to the appropriate device name. 
For example, if `m.destination = "robot"` and `m.destination_device = 
"attention_light"`, the DeviceManager will pass the message to the attention
light attached to the robot.  On the controller side, messages are routed using
the `sendMessage` and `recieveMessage` functions. 

What actually goes through the socket is a string with the form:

    destination.destination_device|source.source_device|delay_time|message

The robot devices and controller functions should never directly access or
manipulate this string, but rather use instances of the class RobotMessage.

variable | what is it? | data type | allowed values | controller default | robot default 
-------- | ----------- | --------- | -------------- | ------------------ | -------------
destination | where the message should go | string | "controller","robot" | "robot" | "controller"
destination_device | device that should parse the message | string | "", any loaded device name | "" | ""
source | message origin | string | "controller","robot" | "controller" | "robot" 
source_device | originating device | string | "", any loaded device name | "" | ""
delay_time | time to delay parsing message (ms) | float | float >= 0 | 0 | 0
message | contents of message | string | depends on device | "" | "" 

Instances of RobotDevice all store an internal `_messages` list that contains all
messages generated since the device was last queried.  These messages can be 
accessed using the `get` method, which returns the current contents of `_messages`
and resets the list.  Messages are passed to the device via the `put` method.  The
`message` string of the RobotMessage is passed to the device. The `put` method 
splits the string on the `~` character.  The first list element is used as a key
for `self._control_dict`, which maps the element to private device methods.  The
second list element is passed as `**kwargs` to that method and should thus look
like a python dictionary.
