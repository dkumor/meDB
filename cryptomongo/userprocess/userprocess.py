import signal

import server

import database.container
import database.cryptfile
import database.mongocontainer

from rootcommander import RootCommander

def run(pipe,logger,config):
    logger.info("Running server process")



    #Set up all requirements for the classes
    rc = RootCommander(pipe)

    def handleSignal(*args):
        server.shutdown_server(rc.shutdown)
    signal.signal(signal.SIGINT,handleSignal)

    database.cryptfile.FileCrypto.rootcommander = rc
    database.container.fileLocation = config["dbdir"]
    database.container.mntLocation = config["mntdir"]
    database.mongocontainer.MongoContainer.logger = logger


    server.runServer(config["port"],config["address"],logger)
