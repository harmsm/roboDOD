#!/usr/bin/env python3
__description__ = \
"""
Tornado instance with multiple threads that allows python to monitor the
user interface for input and the robot for output.

Adapted/expanded from a fantastic tornado + raspberry pi tutorial by asaeed:

http://niltoid.com/blog/raspberry-pi-arduino-tornado/
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-19"
__usage__ = ""
 
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options

import datetime, time, sys
import multiprocessing

import robotConfiguration
from robotDeviceManager import DeviceManager
 
define("port", default=8080, help="run on the given port", type=int)
 
clients = []

class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('web/index.html')
 
class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def __init__(self,*args,**kwargs):  #verbose=False,logfile=None):
        """
        Initialize the class, opening log file etc.
        """

        tornado.websocket.WebSocketHandler.__init__(self,*args,**kwargs)

        self.verbose = False
        self.logfile = "tornado-controller.log"
        self.local_log = open(self.logfile,'a')


    def open(self):
        """
        On open, write to the log file and notify the client that there is a 
        new connection.
        """

        # Record the existance of the new client
        clients.append(self)

        # Write connection to local log
        info_string = "Socket is connected."
        self.writeLog(info_string)

        # Send connection notice to client
        self.write_message("robot|info|%s" % info_string)
 
    def on_message(self, message):
        """
        When a message is recieved, append it to the input_queue.
        """

        if self.verbose:
            info_string = "Tornado recieved \"%s\" from client." % message
            self.writeLog(info_string)
            self.write_message("robot|info|%s" % info_string)

        q = self.application.settings.get('queue')
        q.put(message)
 
    def on_close(self):
        """
        When the socket connection is closed, dump the client and write to the
        log file.
        """

        info_string = "Socket connection closed."
        self.writeLog(info_string)
        self.local_log.close()

        clients.remove(self)

    def writeLog(self,string):
        """
        Write an entry to the log file
        """

        self.local_log.write("%s %s\n" % (str(datetime.datetime.now()),
                                          string))
        self.local_log.flush() 

 
def main(argv=None):
    
    if argv == None:
        argv = sys.argv[1:]
 
    input_queue = multiprocessing.Queue()
    output_queue = multiprocessing.Queue()
 
    dm = DeviceManager(input_queue,output_queue,robotConfiguration.device_list)
    dm.daemon = True
    dm.start()
 
    # wait a second before sending first task
    time.sleep(1)
    dm.input_queue.put("robot|info|initialize")

    # Initailize handler 
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/ws", WebSocketHandler),
            (r"/static/(.*)",tornado.web.StaticFileHandler,{'path':"web/"}),
        ], queue=dm.input_queue
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    dm.input_queue.put("robot|info|Listening on port: %i" % options.port)
 
    def checkResults():
        """
        Basic function to look for output from the robot.
        """

        if not dm.output_queue.empty():
            outputs = dm.output_queue.get()
            for c in clients:
                c.write_message(outputs)

    # Typical tornado.ioloop initialization, except we added a callback in which we 
    # check for robot output 
    mainLoop = tornado.ioloop.IOLoop.instance()
    scheduler = tornado.ioloop.PeriodicCallback(checkResults, 10, io_loop = mainLoop)
    scheduler.start()
    mainLoop.start()
 
if __name__ == "__main__":
    main()
