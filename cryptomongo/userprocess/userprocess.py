
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

threads = []

def cmdrunner(cmd,handler,cmdfnc,cmdargs):


    handler.finish()

class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous   #The requests are funneled to other threads
    def post(self):
        global logger
        global dbhandler

        cmd = self.get_argument("cmd")
        logger.info("SRC: %s CMD: %s"%(self.request.remote_ip,cmd,))
        if (cmd=="ls"):
            logger.info("LS command -> listing open dbs")
            self.write(json.dumps(dbhandler.ls()))
            self.finish()
        elif (cmd=="exists"):
            n = self.get_argument("name")
            logger.info("EXISTS %s",n)
            self.write(json.dumps(dbhandler.exists(n)))
            self.finish()
        elif (cmd=="isopen"):
            n = self.get_argument("name")
            logger.info("ISOPEN %s",n)
            self.write(json.dumps(dbhandler.isopen(n)))
            self.finish()
        else:
            global threads

            #Remove finished threads - a cleanup operation
            for t in threads:
                if not t.isAlive():
                    # get results from thtead
                    t.handled = True
            threads = [t for t in threads if not t.handled]

            #It is one of the asynchronous commands. Run it as such
            t = threading.Thread(target=self.command)
            t.start()
            t.handled = False
            threads.append(t)

    def command(self):
        global logger
        global dbhandler

        cmd = self.get_argument("cmd")

        #Handle the accepted commands
        if (cmd=="connect"):
            n = self.get_argument("name")
            logger.info("CONNECT %s",n)
            self.write(json.dumps(dbhandler.connect(n)))

        elif (cmd=="create"):
            n = self.get_argument("name")
            p = self.get_argument("password")
            s = self.get_argument("size")
            logger.info("CREATE %s",n)
            self.write(json.dumps(dbhandler.create(n,p,s)))
        elif (cmd=="open"):
            n = self.get_argument("name")
            p = self.get_argument("password")
            logger.info("OPEN %s",n)
            self.write(json.dumps(dbhandler.open(n,p)))
        elif (cmd=="close"):
            n = self.get_argument("name")
            logger.info("CLOSE %s",n)
            self.write(json.dumps(dbhandler.close(n)))
        elif (cmd=="panic"):
            n = self.get_argument("name")
            logger.info("PANIC %s",n)
            self.write(json.dumps(dbhandler.panic(n)))
        elif (cmd=="panicall"):
            n = self.get_argument("name")
            logger.info("CLOSE %s",n)
            self.write(json.dumps(dbhandler.panicall()))
        elif (cmd=="delete"):
            n = self.get_argument("name")
            logger.info("DELETE %s",n)
            self.write(json.dumps(dbhandler.delete(n)))

        #These commands should all be fast - so no need to run them in another thread
        else:
            logger.error("Unknown command: \"%s\""%(cmd,))
            self.send_error(500)
        self.finish()



def stopserver():
    global dbhandler
    global rc
    global logger
    global threads
    tornado.ioloop.IOLoop.instance().stop()
    logger.info("Waiting for threads to join...")
    for i in threads:
        i.join()
    logger.info("Closing all containers...")
    dbhandler.closeall()
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
