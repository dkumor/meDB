import os
import signal
from subprocess32 import Popen

import time #Allows timeout for connection
import glob #Allows to list all jar files
import logging

from kazoo.client import KazooClient



class ZooConnection(object):
    """
    Given a folder in which a database is/should be located, it starts a zookeeper server rooted at that location,
    and connects to it. Once close is called, it closes the connection and kills the server.
    """

    def __init__(self,dbfolder,jardir="../jar/",logger=None):

         #Set up logging
        if (logger is None):
            logger = logging.getLogger("ZooKeeper")
            logger.setLevel(logging.INFO)
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(logging.Formatter("%(levelname)s:ZooKeeper:%(created)f - %(message)s"))
            logger.addHandler(ch)
            logger.propagate = False
        self.logger = logger

        self.folder = os.path.relpath(dbfolder) #The path needs to be relative to avoid permissions errors
        self.dbfolder = os.path.join(self.folder,"db")
        #Find an open port
        self.port = get_open_port()

        #Now, make sure that the dbfolder exists
        if not (os.path.isdir(self.folder)):
            if (os.path.exists(self.folder)):
                raise Exception(self.folder+" is not a directory!")
            else:
                os.mkdir(self.folder)
        if not (os.path.isdir(self.dbfolder)):
            if (os.path.exists(self.dbfolder)):
                raise Exception(self.dbfolder+" is not a directory!")
            else:
                os.mkdir(self.dbfolder)

        classpath = ""
        for g in glob.glob(os.path.join(jardir,"*.jar")):
            classpath = classpath + ":"+g
        classpath = classpath[1:]   #get rid of starting :

        #Create the command line
        cmd = ["java","-Dzookeeper.log.dir="+self.folder,"-Dzookeeper.root.logger=INFO,CONSOLE",
                "-cp",classpath,"org.apache.zookeeper.server.quorum.QuorumPeerMain",str(self.port),self.dbfolder]
        
        self.logger.info("Starting zookeeper process")
        self.zoo = Popen(cmd)
        
        self.client = KazooClient(hosts='127.0.0.1:'+str(self.port))
        self.client.start()
        self.logger.info("Connected to zookeeper client")

    def cursor(self):
        return self.client

    def close(self,waitTime=10.):
        if (self.client is not None):
            self.client.stop()
        if (self.zoo is not None):
            self.zoo.send_signal(signal.SIGINT)
            try:
                self.zoo.wait(waitTime)
            except TimeoutExpired:
                self.logger.warn("Expired Timeout - killing process")
                self.zoo.kill()
        self.client = None
        self.zoo = None
    def __del__(self):
        if (self.zoo is not None):
            self.close()

if (__name__=="__main__"):
    import sys
    import shutil
    if (os.path.exists("./tmp")):
        shutil.rmtree("./tmp")

    os.makedirs("./tmp")

    if (len(sys.argv) > 1 and sys.argv[1]=="run"):
        c = ZooConnection("./tmp")
        print "RUNNING",c.port
        raw_input("Press enter to exit")
        c.close()
    else:
        t = time.time()
        c = ZooConnection("./tmp")
        createTime = time.time()-t

        c.cursor().create("/test",b"This is cool",makepath=True)

        t=time.time()
        c.close()
        closeTime = time.time()-t

        t = time.time()
        c = ZooConnection("./tmp")
        openTime = time.time()-t
        dta,stat = c.cursor().get("/test")
        t=time.time()
        c.close()
        closeTime2 = time.time()-t
    
        print dta,stat
        print "Create Time:",createTime
        print "Open Time:",openTime
        print "Close Time",closeTime,closeTime2

    shutil.rmtree("./tmp")