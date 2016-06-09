#!/usr/bin/env python3
__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-19"
__usage__ = ""
 
import signal, sys, time, argparse, os

from rpyBot.messages import RobotMessage
from rpyBot.exceptions import BotConfigurationError

from . import manager, webserver

def start_bot(configuration):
    
    def signal_handler(signal, frame):

        print("Shutting down...")
        sys.stdout.flush()
        
        dm.shutdown()
        time.sleep(5)
        server.shutdown() 

    signal.signal(signal.SIGINT, signal_handler)

    dm = manager.DeviceManager(configuration.device_list)
    dm.start()
 
    # wait a second before sending first task
    time.sleep(1)
    dm.input_queue.put(RobotMessage(destination="robot",
                                    message="initializing"))

    server = webserver.Webserver(dm)
    server.start()

def main(argv=None):
    """
    """

    if argv == None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="rpyBot",description='Start an rpyBot')

    parser.add_argument(dest='config_file',nargs=1,action='store',
                        help='configuration python script')

    args = parser.parse_args(argv)

    config_file = args.config_file[0]

    if not os.path.isfile(config_file):
        err = "\n\nConfiguration file {} not found.\n\n".format(config_file)
        raise BotConfigurationError(err)

    # import configuration file as "configuration" module
    sys.path.append(os.getcwd())
    #c = os.path.join(os.getcwd(),config_file)
    configuration = __import__(config_file[:-3])

    start_bot(configuration)


if __name__ == "__main__":

    main()

