import os, sys

# Import the i2clibraries, with some hacked up path checks to make sure the
# user place the correct libraries in this directory.
script_path = os.path.dirname(os.path.realpath(__file__))
if script_path not in sys.path:
    sys.path.insert(0,script_path)

quick2wire_path = os.path.join(script_path,"quick2wire-python-api")
if quick2wire_path not in sys.path:
    sys.path.insert(0,quick2wire_path)


class ADXL345Accelerometer:

    def __init__(self,port):
    
        from i2clibraries import i2c_adxl345
        
        self.accel = i2c_adxl345.i2c_adxl345(port) 

    def getAxes(self):
    
        return self.accel.getAxes()
