#!/usr/bin/env python3
__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-19"
__usage__ = ""
 
import signal, sys, time, argparse, os

from . import manager, exceptions

def start_bot(configuration,verbosity=0):
    """
    Start the bot up in a frame that can catch ctrl+c.
    """   
 
    def signal_handler(signal, frame):
        """
        Function for catching ctrl+c.
        """

        print("Shutting down...")
        sys.stdout.flush()
        
        dm.shutdown()
        time.sleep(5)

    # start up signal checking thread...
    signal.signal(signal.SIGINT, signal_handler)

    # Start the device manager
    dm = manager.DeviceManager(configuration.device_list,verbosity=verbosity)
    dm.start()
 

def main(argv=None):
    """
    """

    if argv == None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="rpyBot",description='Start an rpyBot')

    parser.add_argument(dest='config_file',nargs=1,action='store',
                        help='configuration python script')

    parser.add_argument("--verbose",dest='verbose',action='store_true',
                        help='be verbose')

    args = parser.parse_args(argv)

    config_file = args.config_file[0]
    verbose = args.verbose

    if not os.path.isfile(config_file):
        err = "\n\nConfiguration file {} not found.\n\n".format(config_file)
        raise exceptions.BotConfigurationError(err)

    # import configuration file as "configuration" module
    sys.path.append(os.getcwd())
    configuration = __import__(config_file[:-3])
    start_bot(configuration,verbose)


if __name__ == "__main__":

    main()

