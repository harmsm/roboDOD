#!/usr/bin/env python3
__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-19"
__usage__ = ""
 
import signal, sys, time

import rpyBot
from rpyBot import manager, configuration, webserver, messages

def main(argv=None):
    
    def signal_handler(signal, frame):
        print("Shutting down...")
        sys.stdout.flush()
        
        dm.shutdown()
        time.sleep(5)
        server.shutdown() 

    signal.signal(signal.SIGINT, signal_handler)

    if argv == None:
        argv = sys.argv[1:]

    dm = rpyBot.manager.DeviceManager(configuration.device_list)
    dm.start()
 
    # wait a second before sending first task
    time.sleep(1)
    dm.input_queue.put(rpyBot.messages.RobotMessage(destination="robot",
                                                    destination_device="dummy",
                                                    message="initializing"))

    server = rpyBot.webserver.Webserver(dm)
    server.start()

if __name__ == "__main__":
    main()
