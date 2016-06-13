__description__ = \
"""
Classes for seving a web site for a remote interface to the robot.
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-19"
__usage__ = ""
 
import multiprocessing

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen

from .. import RobotDevice
from .. import gpio

X = "/home/harmsm/Desktop/rpyBot/rpyBot/devices/web/"
client_list = []

class IndexHandler(tornado.web.RequestHandler):
    """
    Serve main page over http.
    """

    def get(self):
        self.render(X + 'client/index.html')
 
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    """
    Handle web socket requests.  (Conveniently behaves just like a *nix socket). 
    """

    def __init__(self,*args,**kwargs):  
        """
        Initialize the class.
        """

        tornado.websocket.WebSocketHandler.__init__(self,*args,**kwargs)
        self._get_queue = self.application.settings.get("queue")

    def open(self):
        """
        If a new client connects, record it.
        """

        client_list.append(self)
        self._get_queue.put("LOCALMSG client added")

    def on_message(self, message):
        """
        When a message comes from the client, append it to from_client_queue.
        """

        self._get_queue.put(message)

    def on_close(self):
        """
        When the socket connection is closed, dump the client.
        """

        self._get_queue.put("LOCALMSG removed client")
        client_list.remove(self)

class WebInterface(RobotDevice):
    """
    A WebInterfaceDevice that serves an http/javascript website that can be used
    to control the robot remotely.  

    It uses a tornado instance with multiple threads + polling of an input 
    queue.  The original code (much morphed by now!) came from a fantastic 
    tornado/raspberry pi tutorial by asaeed:

    http://niltoid.com/blog/raspberry-pi-arduino-tornado/
    """

    def __init__(self,port=8081,led_gpio=None,name=None):
        """
        Initialize a the class, starting up the input/output queues, the tornado
        handlers, etc.
        """
    
        super(WebInterface, self).__init__(name) 

        # Private variables for handling the web socket 
        self._port = port

        self._led = None
        if led_gpio != None:
            self._led = gpio.LEDIndicatorLight(led_gpio)
        #    self._led.put("off")
             
        # Create a multiprocessing queue to hold messages from the client
        self._get_queue = multiprocessing.Queue()
        self._put_queue = [] 

    def start(self):

        # Initailize handler 
        app = tornado.web.Application(
            handlers=[
                (r"/", IndexHandler),
                (r"/ws", WebSocketHandler),
                (r"/(.*)",tornado.web.StaticFileHandler,{'path':X + "client/"}),
                (r"/js/(.*)",tornado.web.StaticFileHandler,{'path':X + "client/js/"}),
                (r"/css/(.*)",tornado.web.StaticFileHandler,{'path':X + "client/css/"}),
                (r"/fonts/(.*)",tornado.web.StaticFileHandler,{'path':X + "client/fonts/"}),
                (r"/img/(.*)",tornado.web.StaticFileHandler,{'path':X + "client/img/"}),
            ],
            queue=self._get_queue,
        )

        # Create http server
        self._httpServer = tornado.httpserver.HTTPServer(app)
        self._httpServer.listen(self._port)

        # Indicate that robot is ready to listen
        self._queue_message("Listening on port: {:d}".format(self._port))

        # Typical tornado.ioloop initialization, except we added a callback in which we 
        self._mainLoop = tornado.ioloop.IOLoop.instance()
        self._scheduler = tornado.ioloop.PeriodicCallback(self._send_queued_to_client,10,
                                                          io_loop=self._mainLoop)
        # Start the io loop
        self._scheduler.start()
        self._mainLoop.start()

    def get(self):
        """
        Poll the client queue for messages to pass on to the manager.
        """

        # Grab messages from the _get_queue (populated by tornado socket)
        if not self._get_queue.empty():
            from_client = self._get_queue.get() 

            # put these messages into the normal RobotDevice._messages queue,
            # converting to RobotMessage instances in the process.  The LOCALMSG
            # is a hack that lets the tornado client use the queue to send a status
            # string without first converting it into a RobotMessage instance.
            if from_client.startswith("LOCALMSG"):
                self._queue_message("".join(from_client[9:]))
            else:
                self._queue_message(msg_string=from_client)

        # Now do a standard "get" and return all of the messages 
        return self._get_all_messages()
        
    def put(self,message):
        """
        Modified "put" call that, rather than calling a callback, just sticks 
        it into a queue that will be stuffed down the tornado web socket to 
        the client the next time it is polled.
        """
 
        with self._lock:
            self._put_queue.append(message) 

    def stop(self,owner=None):
        """
        Shutdown the tornado instance.
        """

        self._scheduler.stop()
        self._mainLoop.stop()
        self._httpServer.stop()

    def _send_queued_to_client(self):
        """
        Send any messages that have been put in self._input_messages since we 
        last checked, and then send them over the socket to the client.
        """

        with self._lock:
            msg_list = self._put_queue[:]
            self._put_queue = []
        
        #if len(self._client_list) > 0:
        #    self._led.put("on") # <-- SHOULD SEND ROBOT MESSGE HERE
        #else:
        #    self._led.put("off")

        # Send all messages to the client
        for c in client_list:
            for m in msg_list:
                c.write_message(m.as_string())

