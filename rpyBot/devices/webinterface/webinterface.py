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

class IndexHandler(tornado.web.RequestHandler):
    """
    Serve main page over http.
    """

    def get(self):
        self.render('client/index.html')
 
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    """
    Handle web socket requests.  (Conveniently behaves just like a *nix socket). 
    """

    def __init__(self,*args,**kwargs):  
        """
        Initialize the class.
        """

        tornado.websocket.WebSocketHandler.__init__(self,*args,**kwargs)
        self._from_client_queue = self.application.settings.get("queue")
        self._client_list = local_client_list

    def open(self):
        """
        If a new client connects, record it.
        """

        self._client_list.append(self)
        self._from_client_queue.put("added client")

 
    def on_message(self, message):
        """
        When a message comes from the client, append it to from_client_queue.
        """

        self._from_client_queue.put(message)

    def on_close(self):
        """
        When the socket connection is closed, dump the client.
        """

        self._client_list.remove(self)
        self._from_client_queue.put("removed client")

class WebInterfaceDevice(RobotDevice):
    """
    A WebInterfaceDevice that serves an http/javascript website that can be used
    to control the robot remotely.  

    It uses a tornado instance with multiple threads + polling of an input 
    queue.  The original code (much morphed by now!) came from a fantastic 
    tornado/raspberry pi tutorial by asaeed:

    http://niltoid.com/blog/raspberry-pi-arduino-tornado/
    """

    def __init__(self,port=8081,name=None):
        """
        Initialize a the class, starting up the input/output queues, the tornado
        handlers, etc.
        """
    
        super(WebInterfaceDevice, self).__init__(name) 

        # Private variables for handling the web socket 
        self._port = port
        self._client_list = []
        self._input_messages = []

        # Create a multiprocessing queue to hold messages from the client
        self._from_client_queue = multiprocessing.Queue()

        # Initailize handler 
        app = tornado.web.Application(
            handlers=[
                (r"/", IndexHandler),
                (r"/ws", WebSocketHandler),
                (r"/(.*)",tornado.web.StaticFileHandler,{'path':"client/"}),
                (r"/js/(.*)",tornado.web.StaticFileHandler,{'path':"client/js/"}),
                (r"/css/(.*)",tornado.web.StaticFileHandler,{'path':"client/css/"}),
                (r"/fonts/(.*)",tornado.web.StaticFileHandler,{'path':"client/fonts/"}),
                (r"/img/(.*)",tornado.web.StaticFileHandler,{'path':"client/img/"}),
            ],
            queue=self._from_client_queue,
            local_client_list=self._client_list
        )

        # Create http server
        self._httpServer = tornado.httpserver.HTTPServer(app)
        self._httpServer.listen(self._port)

        # Indicate that robot is ready to listen
        self._queue_message("Listening on port: {:d}".format(self._port))

        # Typical tornado.ioloop initialization, except we added a callback in which we 
        # check for robot output 
        self._mainLoop = tornado.ioloop.IOLoop.instance()
        self._scheduler = tornado.ioloop.PeriodicCallback(self._send_queued_to_client,10,
                                                          io_loop=self.mainLoop)
        # Start the io loop
        self._scheduler.start()
        self._mainLoop.start()


    def get(self):
        """
        Poll the client queue for messages to pass on to the manager.
        """

        # Grab messages from the _from_client_queue (populated by tornado socket)
        from_client = self._from_client_queue.get()
        
        # put these messages into the normal RobotDevice._messages list,
        # converting to RobotMessage instances in the process
        for c in from_client:
            self._queue_message(msg_string=c)

        # Not do a standard "get" and return all of the messages 
        return self._get_all_messages
        
    def put(self,message):
        """
        Modified "put" call that, rather than calling a callback, just appends
        the message to a message list that is stuffed down the tornado 
        web socket to the client. 
        """
  
        with self._lock:
            self._input_messages.append(message)

    def shutdown(self):
        """
        Shutdown the tornado instance.
        """

        self.scheduler.stop()
        self.mainLoop.stop()
        self.httpServer.stop()

    def _send_queued_to_client(self):
        """
        Send any messages that have been put in self._input_messages since we 
        last checked, and then send them over the socket to the client.
        """

        with self._lock:

            msg_list = []
            if len(self._input_messages) > 0:
                msg_list = self._input_messages[:]
                self._input_messages = []

                # Send all messages to the client
                for c in self._client_list:
                    for m in msg_list:
                        c.write_message(m.as_string())
