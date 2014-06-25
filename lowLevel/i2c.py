import os

# Import the i2clibraries, with some hacked up path checks to make sure the
# user place the correct libraries in this directory.
script_path = os.path.dirname(os.path.realpath(__file__))

try:
    os.environ["QUICK2WIRE_API_HOME"]
except KeyError:
    os.environ["QUICK2WIRE_API_HOME"] = script_path

try:
    python_path = os.environ["PYTHONPATH"]
    if script_path not in python_path.split(":"):
        os.environ["PYTHONPATH"] = "%s:%s" % (script_path,python_path)
except KeyError:
    os.environ["PYTHONPATH"] = script_path
        

if not os.path.isdir(os.path.join(script_path,"i2clibraries")):
    err = "Did you copy the i2clibraries into %s?" % script_path
    raise Exception(err)

if not os.path.isdir(os.path.join(script_path,"quick2wire-python-api")):
    err = "Did you copy the quick2wire-pytho-api into %s?" % script_path
    raise Exception(err)
 
from i2clibraries import i2c_adxl345


