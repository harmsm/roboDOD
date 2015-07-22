#!/usr/bin/env python3
__description__ = \
"""
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-19"
__usage__ = ""
 
import signal
import manager, configuration, webserver, messages
 
def main(argv=None):
    
    def signal_handler(signal, frame):
        dm.shutdown()

    signal.signal(signal.SIGINT, signal_handler)

    if argv == None:
        argv = sys.argv[1:]

    dm = manager.DeviceManager(configuration.device_list)
    dm.start()
 
    # wait a second before sending first task
    time.sleep(1)
    dm.input_queue.put(messages.RobotMessage(destination="robot",
                                             destination_device="dummy",
                                             message="initializing"))

    webserver.start(dm)

if __name__ == "__main__":
    main()
