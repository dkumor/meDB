
import tornado.ioloop
import tornado.web

import json

logger = None
class MainHandler(tornado.web.RequestHandler):

    def post(self):
        global logger
        cmd = self.get_argument("cmd")
        logger.info("CMD: %s"%(cmd,))
        self.send_error(500)



def stopserver(killfnc):
    tornado.ioloop.IOLoop.instance().stop()
    killfnc()

isstopping = False
def shutdown_server(killfnc):
    global isstopping
    global logger
    if (isstopping==False):
        logger.critical("Shutting down server")
        isstopping = True
        tornado.ioloop.IOLoop.instance().add_callback_from_signal(stopserver,killfnc)



def runServer(portnumber,interface,log):
    MainHandler.logger = logger
    global logger
    logger = log
    application = tornado.web.Application([
        (r"/",MainHandler)
    ])

    application.listen(portnumber,address=interface)
    logger.info("Started server at %s:%i"%(interface,portnumber))
    tornado.ioloop.IOLoop.instance().start()
