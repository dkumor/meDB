import logging
logger = logging.getLogger("MongoDB")

import os
import signal
from subprocess32 import Popen

import time #Allows timeout for connection
from pymongo import MongoClient

from ..connection import Connection

class MongoDB(object):
    """
    Given a folder in which a database is/should be located, it starts a mongoDB server rooted at that location,
    and connects to it. Once close is called, it closes the connection and kills the server.
    """
      
    def __init__(self,chost,hostname,port,dbpath="./mongodb"):
        logger.info("Setting up...")
        self.mongod= None
        self.client = None
        
        #Create dbpath if it doesn't exist
        if not (os.path.isdir(dbpath)):
            if (os.path.exists(dbpath)):
                logger.error("'%s' is not a directory!",dbpath)
                raise Exception(dbpath+" is not a directory!")
            else:
                logger.warning("Creating path '%s'",dbpath)
                os.mkdir(dbpath,0700)

                #Make sure there is enough free space on the disk
                disk =  os.statvfs(dbpath)
                disk = float(disk.f_frsize*disk.f_bavail)/1024/1024
                if (disk < 512.0):
                    logger.error("Not enough free space to create database! (%.2fMB)",disk)
                    os.rmdir(dbpath)    #Remove the directory
                    raise Exception("Not enough free space to create database!")
                
        #Make sure there is enough free space on the disk (otherwise warn about free space)
        disk =  os.statvfs(dbpath)
        disk = float(disk.f_frsize*disk.f_bavail)/1024/1024


        logger.info("Loading config from server")
        host = hostname+":"+str(port)
        
        self.connection = Connection(chost,"mongodb",host)

        #Gets the configuration for the server
        cfg = self.connection.config

        #Create the command line for MongoDB
        cmd = ["mongod","--dbpath",dbpath,"--port",str(port),
                        "--bind_ip",hostname,"--quiet","--nohttpinterface"]
        if (disk <= 2048):
            cmd.append("--smallfiles")
            logger.warn("Only %.2fMB free space on disk. Using smallfiles.",disk)


        if (cfg != None):
            logger.info("Extra config loaded from server: %s",str(cfg))
            cmd = cmd + cfg
        else:
            logger.info("No extra config detected. Continuing with defaults.")

        
        logger.info("Mongo Command: "+str(cmd))
        #Start the database
        self.mongod = Popen(cmd)
        
        #Starts the client - and gives it 2 minutes to figure out whether it is going to connect or not.
        #This is dependent on whether the database daemon is successfully starting up in the background.
        #The extremely long wait time is because some old laptops can take very long to create a database.
        #The wait time is not an issue, since we check if mongoDB crashed if we can't connect - so in effect
        #the actual wait time is at most a couple seconds if the database actually fails to start.
        t = time.time()
        while (time.time() - t < 120.0 and self.client==None):
            try:
                self.client = MongoClient(port=port)
            except:
                time.sleep(0.1)
                #If the process crashed for some reason, don't continue waiting like an idiot
                if (self.mongod.poll()!=None):
                    logger.error("MongoDB did not start correctly.")
                    self.mongod = None
                    break
        if (self.client==None):
            self.close()
            raise Exception("Could not connect to database")
            
    def cursor(self):
        return self.client
    
    def close(self,waitTime=10.):
        logger.info("shutting down server")
        """Closes and cleans up the database"""
        if (self.connection is not None):
            self.connection.close()

        if (self.client!=None):
            self.client.close()
            
        if (self.mongod!=None):
            self.mongod.send_signal(signal.SIGINT)
            try:
                self.mongod.wait(waitTime)
            except TimeoutExpired:
                logger.warn("Expired Timeout - killing process")
                self.mongod.kill()
            
        self.mongod = None
        self.client = None
        self.connection = None
        
    def __del__(self):
        if (self.mongod is not None):
            self.close()
