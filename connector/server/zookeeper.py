import logging
logger = logging.getLogger("ZooKeeper")

import glob
import os

from serverbase import BaseServer
from kazoo.client import KazooClient


class Zookeeper(BaseServer):
    """
    Given a setup, starts the Zookeeper server with the given configuration options
    """

    def __init__(self,hostname,port,dbpath="./zookeeper",jardir="./bin/jar/"):
        BaseServer.__init__(self,"zookeeper", hostname+":"+str(port),hostname,port,dbpath,logger)
        
        #Create the command line
        cmd = ["java","-Dzookeeper.log.dir=./","-Dzookeeper.root.logger=INFO,CONSOLE",
                "-cp",self.classpath(jardir),"org.apache.zookeeper.server.quorum.QuorumPeerMain",str(self.port),self.dbpath]
        
        self.runServer(cmd)

        self.connect()
        #Register!
        self.connection.registerme()

        logger.info("server running...")
            


if (__name__=="__main__"):
    from ..setup.server import ServerSetup
    
    
    s = ServerSetup(description="Zookeeper server standalone",bindir="./bin")
    
    try:
        zk = Zookeeper(s.hostname,s.port)
        raw_input()
        zk.close()
    except:
        s.close()
        raise

    s.close()
    

    """
    logging.basicConfig()
    zk = Zookeeper("localhost",1337)
    print "RUNNING"
    raw_input()
    zk.close()
    """
