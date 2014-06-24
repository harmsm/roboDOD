###############################################################################################################                                                          
# Program Name: Browser_Client_Coder.html                                     
# ================================     
# This code is for controlling a robot by a web browser using web sockets                            
# http://www.dexterindustries.com/                                                                
# History
# ------------------------------------------------
# Author     Comments
# Joshwa     Initial Authoring
#                                                                  
# These files have been made available online through a Creative Commons Attribution-ShareAlike 3.0  license.
# (http://creativecommons.org/licenses/by-sa/3.0/)           
#
###############################################################################################################

import time
from robotDevices import TwoMotorDriveSteer, RangeFinder 

import threading
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template

#Initialize TOrnado to use 'GET' and load index.html
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        loader = tornado.template.Loader(".")
        self.write(loader.load("index.html").generate())

#Code for handling the data sent from the webpage
class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):

        print('connection opened...')
        self.m = TwoMotorDriveSteer(13,15,7,11)
        self.rangeFinder = RangeFinder(16,18)

    def on_message(self, message):      # receives the data from the webpage and is stored in the variable message

        print(message)
        if message == "get":
            self.rangeFinder.sendData(message)
            time.sleep(0.1)
            x = self.rangeFinder.getData()
            print(x)
            
        else:
            self.m.sendData(message)
       
    def on_close(self):
        print('connection closed...')
        self.m.sendData("stop")
        self.m.sendData("coast")
        self.m.sendData("center")


application = tornado.web.Application([
  (r'/ws', WSHandler),
  (r'/', MainHandler),
  (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./resources"}),
])

class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print("Ready")
        while running:
            time.sleep(.2)              # sleep for 200 ms

if __name__ == "__main__":
    running = True
    thread1 = myThread(1, "Thread-1", 1)
    thread1.setDaemon(True)
    thread1.start()  
    application.listen(8080)              #starts the websockets connection
    tornado.ioloop.IOLoop.instance().start()
  

