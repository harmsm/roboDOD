__description__ = \
"""
Class for serving a web site for a remote interface to the robot.
"""
__author__ = "Michael J. Harms"
__date__ = "2014-06-19"
__usage__ = ""

HACK_PATH = "/home/harmsm/Desktop/rpyBot/rpyBot/devices/web/client/" 
 
import multiprocessing, os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen

from .. import RobotDevice, gpio

class IndexHandler(tornado.web.RequestHandler):
    """
    Serve main page over http.
    """

    def __init__(self,*args,**kwargs):

        # Get the index file
        self._client_path = kwargs["client_path"]
        self._client_list = kwargs["client_list"]
        self._index_file = os.path.join(self._client_path,"index.html")
        self._block_file = os.path.join(self._client_path,"blocked.html")

        # Get rid of the extra kwarg and call the path inint function
        kwargs.pop("client_list")
        kwargs.pop("client_path")
        super(IndexHandler, self).__init__(*args,**kwargs)
        
    def get(self):
        """
        Serve the main page over http.
        """

        if len(self._client_list) == 0:
            self.render(self._index_file)
        else:
            self.render(self._block_file)
 
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    """
    Handle web socket requests.  (Conveniently behaves just like a *nix socket). 
    """

    def __init__(self,*args,**kwargs):  
        """
        Initialize the class.
        """

        # Client list is a pointer to a list held in the device that is the
        # list of clients
        self._client_list = kwargs["client_list"]
        kwargs.pop("client_list")

        tornado.websocket.WebSocketHandler.__init__(self,*args,**kwargs)
        self._get_queue = self.application.settings.get("queue")

    def open(self):
        """
        If a new client connects, record it.
        """

        self._client_list.append(self)
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
        self._client_list.remove(self)

class WebInterface(RobotDevice):
    """
    A WebInterfaceDevice that serves an http/javascript website that can be used
    to control the robot remotely.  

    It uses a tornado instance and polling to pass messages back and forth.  The
    original code (much morphed by now!) came from a fantastic tornado/raspberry
    pi tutorial by asaeed:

    http://niltoid.com/blog/raspberry-pi-arduino-tornado/
    """

    def __init__(self,port=8081,led_gpio=None,name=None,web_path=None):
        """
        Initialize a the class, starting up the input/output queues, the tornado
        handlers, etc.
        """
    
        super(WebInterface, self).__init__(name) 

        # Private variables for handling the web socket 
        self._port = port

        # Stub.  This will (someday) directly associate an led with the device 
        # so the device has a status light. 
        self._led = None
        if led_gpio != None:
            self._led = gpio.IndicatorLight(led_gpio)
            
        self._web_path = web_path
        if self._web_path == None:
            self._web_path = HACK_PATH
 
        # Create a multiprocessing queue to hold messages from the client
        self._get_queue = multiprocessing.Queue()
        self._put_queue = multiprocessing.Queue()
        self._client_list = []

    def start(self):
        """
        Start up the tornado server.
        """

        # Initailize handler 
        app = tornado.web.Application(
            handlers=[
                (r"/", IndexHandler,{'client_path':self._web_path,
                                     'client_list':self._client_list}),
                (r"/ws", WebSocketHandler,{"client_list":self._client_list}),
                (r"/(.*)",tornado.web.StaticFileHandler,{'path':self._web_path}),
                (r"/js/(.*)",tornado.web.StaticFileHandler,{'path':os.path.join(self._web_path,"js")}),
                (r"/css/(.*)",tornado.web.StaticFileHandler,{'path':os.path.join(self._web_path,"css")}),
                (r"/fonts/(.*)",tornado.web.StaticFileHandler,{'path':os.path.join(self._web_path,"fonts")}),
                (r"/img/(.*)",tornado.web.StaticFileHandler,{'path':os.path.join(self._web_path,"img")}),
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
        Poll the client queue for messages.
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
        Modified version of RobotDevice put method that sticks the message into
        a queue that will be stuffed down the tornado web socket to the client
        the next time it is polled.
        """

        self._put_queue.put(message)


    def stop(self,owner=None):
        """
        Stop the tornado instance.
        """

        try: 
            self._mainLoop.stop()
        except AttributeError:
            pass

        try:
            self._scheduler.stop()
        except AttributeError:
            pass

        try:
            self._httpServer.stop()
        except AttributeError:
            pass

    def _send_queued_to_client(self):
        """
        Send any messages that have been put in self._input_messages since we 
        last checked, and then send them over the socket to the client.
        """

        if not self._put_queue.empty():
            m = self._put_queue.get()
    
            # Send all messages to the client
            for c in self._client_list:
                c.write_message(m.as_string())

