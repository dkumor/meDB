import logging


logger = logging.getLogger("ZooKeeper")

import glob
import os
import signal
from subprocess32 import Popen

from kazoo.client import KazooClient

from ..connection import Connection

class Zookeeper(object):
    """
    Given a setup, starts the Zookeeper server with the given configuration options
    """

    def __init__(self,hostname,port,dbpath="./zookeeper",jardir="./bin/jar/"):
        #Add on the "zookeeper" prefix to the path
        self.folder = dbpath
        self.port = port

        logger.info("Setting up...")

        if not (os.path.isdir(self.folder)):
            if (os.path.exists(self.folder)):
                raise Exception(self.folder+" is not a directory!")
            else:
                logger.warning("Creating path '%s'",self.folder)
                os.mkdir(self.folder,0700)

        #Now we have to add all the classes in jar files
        classpath = ""
        for g in glob.glob(os.path.join(jardir,"*.jar")):
            classpath = classpath + ":"+g
        classpath = classpath[1:]   #get rid of starting :
        
        #Create the command line
        cmd = ["java","-Dzookeeper.log.dir=./","-Dzookeeper.root.logger=INFO,CONSOLE",
                "-cp",classpath,"org.apache.zookeeper.server.quorum.QuorumPeerMain",str(self.port),self.folder]
        
        logger.info("Starting server on port %i...",self.port)
        self.zoo = Popen(cmd)

        host = hostname+":"+str(self.port)

        self.connection = Connection(host,"zookeeper",host)

        logger.info("server running...")

    def close(self,waitTime=10.):
        logger.info("Shutting down server...")
        if (self.connection is not None):
            self.connection.close()
        if (self.zoo is not None):
            self.zoo.send_signal(signal.SIGINT)
            try:
                self.zoo.wait(waitTime)
            except TimeoutExpired:
                logger.warn("Expired close timeout - killing process")
                self.zoo.kill()
        self.connection=None
        self.zoo=None
    def __del__(self):
        if (self.zoo is not None):
            self.close()
            


if (__name__=="__main__"):
    from ..setup.server import ServerSetup
    #logging.basicConfig()
    s = ServerSetup(description="Zookeeper server standalone",bindir="./bin")
    
    try:
        zk = Zookeeper(s.hostname,s.port)
        raw_input()
        zk.close()
    except:
        s.close()
        raise

    s.close()