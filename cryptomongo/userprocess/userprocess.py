
import tornado.ioloop
import tornado.web

import json

import signal

from rootcommander import RootCommander
from mongostore import DatabaseManager

def run(pipe,logger,config):
    logger.info("Running server process")

    #Set up all requirements for the classes
    rc = RootCommander(pipe)



    database.cryptfile.FileCrypto.rootcommander = rc
    database.container.fileLocation = config["dbdir"]
    database.container.mntLocation = config["mntdir"]
    database.mongocontainer.MongoContainer.logger = logger


    server.runServer(config["port"],config["address"],logger)




#The three global variables
logger = None
dbhandler = None
rc = None

class MainHandler(tornado.web.RequestHandler):

    def post(self):
        global logger
        cmd = self.get_argument("cmd")
        logger.info("CMD: %s"%(cmd,))

        #Handle the accepted commands
        if (cmd=="connect"):
            pass
        elif (cmd=="create"):
            pass
        elif (cmd=="open"):
            pass
        elif (cmd=="close"):
            pass
        elif (cmd=="panic"):
            pass
        elif (cmd=="panicall"):
            pass
        elif (cmd=="ls"):
            pass
        elif (cmd=="delete"):
            pass
        elif (cmd=="exists"):
            pass
        elif (cmd=="isopen"):
            pass

        self.send_error(500)



def stopserver():
    tornado.ioloop.IOLoop.instance().stop()
    rc.shutdown()

isstopping = False
def shutdown_server(*args):
    global isstopping
    global logger
    if (isstopping==False):
        isstopping = True
        logger.critical("Shutting down server")
        tornado.ioloop.IOLoop.instance().add_callback_from_signal(stopserver)



def run(pipe,log,config):
    #Set the logger
    global logger
    logger = log

    #The pipe from the rootprocess allows userspace processes to run specific commands as root
    global rc
    rc = RootCommander(pipe)

    #Now create the database handler, which will manage all database processes
    global dbhandler
    dbhandler = DatabaseManager(rc,config["dbdir"],config["mntdir"])

    #Handle the ctrl+C signal
    signal.signal(signal.SIGINT,shutdown_server)


    application = tornado.web.Application([
        (r"/",MainHandler)
    ])

    portnumber = config["port"]
    interface = config["address"]

    application.listen(portnumber,address=interface)
    logger.info("Started server at %s:%i"%(interface,portnumber))
    tornado.ioloop.IOLoop.instance().start()
