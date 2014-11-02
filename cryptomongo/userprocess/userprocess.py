
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
            self.send_error(500)
            """
            elif (cmd=="create"):
                self.send_error(500)
            elif (cmd=="open"):
                self.send_error(500)
            elif (cmd=="close"):
                self.send_error(500)
            elif (cmd=="panic"):
                self.send_error(500)
            elif (cmd=="panicall"):
                self.send_error(500)
            elif (cmd=="delete"):
                self.send_error(500)
            """
        #These commands should all be fast - so no need to run them in another thread
        elif (cmd=="ls"):
            logger.info("LS command -> listing open dbs")
            self.write(json.dumps(dbhandler.ls()))
        elif (cmd=="exists"):
            n = self.get_argument("name")
            logger.info("EXISTS %s",n)
            self.write(json.dumps(dbhandler.exists(n)))
        elif (cmd=="isopen"):
            n = self.get_argument("name")
            logger.info("ISOPEN %s",n)
            self.write(json.dumps(dbhandler.isopen(n)))

        else:
            logger.error("Unknown command: \"%s\""%(cmd,))
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
    log.info("Setting up user process as %(user)s"%config)
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
