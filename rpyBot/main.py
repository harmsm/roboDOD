#!/usr/bin/env python3
__description__ = \
"""
Program that, when run, starts up the robot.  This will be installed as rpyBot 
into the executable path. 
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-19"
__usage__ = "called from command line. usage defined by argparse"
 
import signal, sys, time, argparse, os

from . import manager, exceptions

def start_bot(configuration,verbosity=0):
    """
    Start the bot up in a frame that can catch ctrl+c.
    """   
 
    dm = manager.DeviceManager(configuration.device_list,verbosity=verbosity)

    def signal_handler(signal, frame):
        """
        Function for catching ctrl+c.
        """
        dm.shutdown()
        print("Shutting down...")
        sys.exit()

    # start up signal checking thread...
    signal.signal(signal.SIGINT, signal_handler)

    # Start the device manager
    dm.start()
 

def main(argv=None):
    """
    Parse the command line and start up the robot.
    """

    if argv == None:
        argv = sys.argv[1:]

    # Construct parser
    parser = argparse.ArgumentParser(prog="rpyBot",description='Start an rpyBot')

    parser.add_argument(dest='config_file',nargs=1,action='store',
                        help='configuration python script')
    parser.add_argument("--verbose",dest='verbose',action='store_true',
                        help='be verbose')
    args = parser.parse_args(argv)

    # Grab the configuration file
    config_file = args.config_file[0]
    verbose = args.verbose
    if not os.path.isfile(config_file):
        err = "\n\nConfiguration file {} not found.\n\n".format(config_file)
        raise exceptions.BotConfigurationError(err)

    # import configuration file as "configuration" module
    sys.path.append(os.getcwd())
    configuration = __import__(config_file[:-3])
    start_bot(configuration,verbosity=verbose)

# If called from the command line
if __name__ == "__main__":
    main()

