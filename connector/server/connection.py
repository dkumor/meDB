
from kazoo.client import KazooClient, KazooState

import json

import socket   #The hostname is part of socket
import os       #Can get PID thru os

class Connection(object):
    def __init__(self,zoohosts,cname="client",rootpath="/connector"):
        self.name = socket.gethostname() + ":" + str(os.getpid())
        self.cname = cname
        self.rootpath = rootpath

        #Connect to the zookeeper instance
        self.zoo = KazooClient(hosts=zoohosts)
        self.zoo.add_listener(self.state_listener)
        self.zoo.start()

        self.registerme()


    def registerme(self):
        #Notifies the zookeeper that this server is connected
        basepath = self.rootpath+"/"+self.cname+"/"+ self.name + "/"

        #Creates the entire pathway to db list
        self.zoo.ensure_path(basepath+"db")
        #Create ephemeral node which represents connection status of this node
        self.zoo.create(basepath+"isconnected",ephemeral=True)
        

    def state_listener(self,state):
        if (state == KazooState.CONNECTED):
            print "Connected"
        elif (state == KazooState.SUSPENDED):
            print "Got disconnected"
        else:
            print "Connection lost."

    def close(self):
        self.zoo.stop()

    def config(self):
        #Load the general configuration for objects of the given type
        data,stat = self.zoo.get(self.rootpath+"/"+self.cname)
        return json.loads(data.decode('utf-8'))


if (__name__=="__main__"):

    import shutil
    import time


    if (os.path.exists("./tmp")):
        shutil.rmtree("./tmp")

    os.makedirs("./tmp")

    from server import ZooServer

    import logging
    logging.basicConfig()

    zooc = ZooServer("./tmp")


    zh = "localhost:"+str(zooc.port)
    
    c = Connection(zh)
    c.close()
    

    time.sleep(1.0)
    zooc.close()

    shutil.rmtree("./tmp")