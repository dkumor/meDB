import logging
logger = logging.getLogger("MongoDB")

import os

from serverbase import BaseServer

import time #Allows timeout for connection
from pymongo import MongoClient



class MongoDB(BaseServer):
    """
    Given a folder in which a database is/should be located, it starts a mongoDB server rooted at that location,
    and connects to it. Once close is called, it closes the connection and kills the server.
    """
    
    def __init__(self,chost,hostname,port=None,dbpath="./mongodb"):
        BaseServer.__init__(self,"mongodb",chost,dbpath,logger,hostname,port,minspace = 512.0)
        self.connect()
        
        #Create the command line for MongoDB
        cmd = ["mongod","--dbpath",self.dbpath,"--port",str(self.port),
                        "--bind_ip",hostname,"--quiet","--nohttpinterface"]
        
        disk = self.checkDiskSpace()
        if (disk <= 2048):
            cmd.append("--smallfiles")
            logger.warn("Only %.2fMB free space on disk. Using smallfiles.",disk)
        
        self.addConfig({"cmd": cmd})

        #Gets the configuration for the server
        self.addConfig(self.connection.config)

        self.writeConfig()
        self.runServer()
        
        #Starts the client - and gives it 2 minutes to figure out whether it is going to connect or not.
        #This is dependent on whether the database daemon is successfully starting up in the background.
        #The extremely long wait time is because some old laptops can take very long to create a database.
        #The wait time is not an issue, since we check if mongoDB crashed if we can't connect - so in effect
        #the actual wait time is at most a couple seconds if the database actually fails to start.
        t = time.time()
        while (time.time() - t < 120.0 and self.client is None):
            try:
                self.client = MongoClient(port=self.port)
            except:
                time.sleep(0.1)
                #If the process crashed for some reason, don't continue waiting like an idiot
                if (self.server.poll() is not None):
                    logger.error("MongoDB did not start correctly.")
                    self.server = None
                    break
        if (self.client==None):
            self.close()
            raise Exception("Could not connect to database")

        #The mongoDB connection is no longer necessary
        self.client.close()
        self.client = None

        #Register the client as ready
        self.connection.registerme()
            
        logger.info("server running...")
