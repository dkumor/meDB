import os
import signal
from subprocess32 import Popen

import time #Allows timeout for connection
from pymongo import MongoClient

class Connection(object):
    """
    Given a folder in which a database is/should be located, it starts a mongoDB server rooted at that location,
    and connects to it. Once close is called, it closes the connection and kills the server.
    """
    
    #MongoDB server runs on a port - each connection needs its on port. These variables manage port numbers
    freedPorts = []     #Ports that have been freed by previous connections closing
    startPort = 27018   #The port at which to start adding new connections once there are no free ports
    
    def __init__(self,dbfolder):
        self.folder = os.path.abspath(dbfolder)
        
        #Find a port to connect on
        if (len(self.freedPorts) > 0):
            self.port = self.freedPorts.pop()
        else:
            self.port = self.startPort
            self.startPort += 1
        
        #Check if the database folder exists
        if not (os.path.isdir(self.folder)):
            raise Exception("Database folder does not exist")
        
        print self.folder,self.port
        
        #Start MongoDB server
        self.mongod = Popen(["mongod","--dbpath",self.folder,"--port",str(self.port),
                        "--bind_ip","127.0.0.1","--smallfiles","--quiet"])
        
        #Starts the client - and gives it 20 seconds to figure out whether it is going to connect or not.
        #This is dependent on whether the database daemon is successfully starting up in the background
        self.client = None
        t = time.time()
        while (time.time() - t < 20.0 and self.client==None):
            try:
                self.client = MongoClient(port=self.port)
            except:
                time.sleep(0.1)
        if (self.client==None):
            self.close()
            raise Exception("Could not connect to database")
            
    def cursor(self):
        return self.client
    
    def close(self,waitTime=10.):
        """Closes and cleans up the database"""
        
        if (self.client!=None):
            self.client.close()
            
        if (self.mongod!=None):
            self.mongod.send_signal(signal.SIGINT)
            try:
                self.mongod.wait(waitTime)
            except TimeoutExpired:
                print "Expired Timeout - killing process"
                self.mongod.kill()
            #Add the port to the pool of free ports
            self.freedPorts.append(self.port)
            
        self.mongod = None
        self.client = None
        
    def __del__(self):
        if (self.mongod != None):
            self.close()
        
if (__name__=="__main__"):
    import shutil
    os.makedirs("./tmp")
    t = time.time()
    c = Connection("./tmp")
    createTime = time.time()-t
    db = c.cursor().db.input
    db.insert({"hi": "hello","wee":"waa"})
    t=time.time()
    c.close()
    closeTime = time.time()-t
    t = time.time()
    c = Connection("./tmp")
    openTime = time.time()-t
    db = c.cursor().db.input
    dta = db.find_one({"hi":"hello"})
    t=time.time()
    c.close()
    closeTime2 = time.time()-t
    shutil.rmtree("./tmp")
    print dta
    print "Create Time:",createTime
    print "Open Time:",openTime
    print "Close Time",closeTime,closeTime2
        
