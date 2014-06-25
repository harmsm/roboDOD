roboDOD
=======

software for controlling an autonomous car via a raspberry pi

#Notes:

To use a device with i2c, you need to enable the I2C kernel modules and
then copy the quick2wire and i2clibraries into the roboDOD/lowLevel 
directory.  

    cd roboDOD/lowLevel
    git clone https://github.com/quick2wire/quick2wire-python-api.git
    git clone https://bitbucket.org/thinkbowl/i2clibraries.git

roboDOD will do the rest, in terms of setting environment variables etc.
