import logging
logger = logging.getLogger("ZooKeeper")

import glob
import os

from serverbase import BaseServer
from kazoo.client import KazooClient


class Zookeeper(BaseServer):
    """
    Given a setup, starts the Zookeeper server with the given configuration options


    TODO: 
    
    INFO autopurge.purgeInterval set to 0 (org.apache.zookeeper.server.DatadirCleanupManager)
    ZooKeeper:INFO - -- [2014-12-29 10:10:05,439] INFO Purge task is not scheduled. (org.apache.zookeeper.server.DatadirCleanupManager)
    WHAT DOES THIS MEAN??? I know that I should purge zookeeper old data files after a while -but is there a setting for this (need to check when have internet)
    

    CHECK BIND PORT
    """

    def __init__(self,hostname,port=None,dbpath="./zookeeper",jardir="./bin/jar/"):
        BaseServer.__init__(self,"zookeeper", hostname+":"+str(port),dbpath,logger,hostname,port)
        
        #Create the command line
        cmd = ["java","-Dzookeeper.log.dir="+self.folder,"-Dlog4j.configuration=file:"+os.path.join(self.folder,"log4j.properties"),
               "-cp",self.classpath(jardir),"org.apache.zookeeper.server.quorum.QuorumPeerMain",os.path.join(self.folder,"zookeeper.properties")]
        
        logproperties = self.configDefaults["log4j.properties"]
        logproperties["org.apache.zookeeper.server.DatadirCleanupManager"] = "org.apache.log4j.ConsoleAppender"
        logproperties["org.apache.zookeeper.server.DatadirCleanupManager.layout"] = "org.apache.log4j.PatternLayout"
        logproperties["log4j.appender.stdout.layout.ConversionPattern"]="[%d] %p %m (%c)%n"

        self.addConfig({"cmd": cmd,"log4j.properties": logproperties,
                        "zookeeper.properties":{
                            "dataDir": self.dbpath,
                            "clientPort": str(self.port)
                            }})
        self.writeConfig()
        self.runServer()

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
