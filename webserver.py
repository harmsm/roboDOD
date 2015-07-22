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

import datetime, time, sys, signal, logging
import multiprocessing

import configuration
from messages import RobotMessage
 
define("port", default=8081, help="run on the given port", type=int)
 
clients = []

class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('client/index.html')
 
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
        self.write_message(RobotMessage(destination="controller",
                                        message=info_string).as_string())

        self.q = self.application.settings.get('queue')
 
    def on_message(self, message):
        """
        When a message is recieved, append it to the input_queue.
        """

        if self.verbose:
            info_string = "Tornado recieved \"{:s}\" from client.".format(message)
            self.writeLog(info_string)
            self.write_message(RobotMessage(destination="controller",
                                            message=info_string).as_string())

        m = RobotMessage()
        m.from_string(message) 
        self.q.put(m)

        if self.verbose:
            self.writeLog("Queue size: {:d}\n".format(self.q.qsize()))

    def on_close(self):
        """
        When the socket connection is closed, dump the client and write to the
        log file.
        """

        info_string = "Socket connection closed."
        self.writeLog(info_string)
        self.local_log.close()
        
        # Turn off the status light indicating that we're connected.
        self.q.put(RobotMessage(destination="robot",
                                destination_device="client_connected_light",
                                message="off").as_string())

        clients.remove(self)

    def writeLog(self,string):
        """
        Write an entry to the log file
        """

        self.local_log.write("{:s} {:s}\n".format(str(datetime.datetime.now()),
                                                  string))
        self.local_log.flush() 

def start(dm):

    # Initailize handler 
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/ws", WebSocketHandler),
            (r"/(.*)",tornado.web.StaticFileHandler,{'path':"client/"}),
            (r"/js/(.*)",tornado.web.StaticFileHandler,{'path':"client/js/"}),
            (r"/css/(.*)",tornado.web.StaticFileHandler,{'path':"client/css/"}),
            (r"/fonts/(.*)",tornado.web.StaticFileHandler,{'path':"client/fonts/"}),
            (r"/img/(.*)",tornado.web.StaticFileHandler,{'path':"client/img/"}),
        ], queue=dm.input_queue
    )

    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)

    # Indicate that robot is ready to listen
    dm.input_queue.put(RobotMessage(destination="robot",
                                    destination_device="dummy",
                                    message="Listening on port: {:d}".format(options.port)))
    dm.input_queue.put(RobotMessage(destination="robot",
                                    destination_device="system_up_light",
                                    message="on"))
 
    def checkResults():
        """
        Look for output from the robot.
        """

        if not dm.output_queue.empty():
            m = dm.output_queue.get()
            if m.check_delay() == True:
                for c in clients:
                    c.write_message(m.as_string())
            else:
                dm.output_queue.put(m)

    # Typical tornado.ioloop initialization, except we added a callback in which we 
    # check for robot output 
    mainLoop = tornado.ioloop.IOLoop.instance()
    scheduler = tornado.ioloop.PeriodicCallback(checkResults, 10, io_loop = mainLoop)
    scheduler.start()
    mainLoop.start()

