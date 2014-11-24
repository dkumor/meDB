
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

        self.zoo.ensure_path(self.rootpath+"/"+self.cname)
        self.zoo.create(self.rootpath+"/"+self.cname+"/" + self.name,ephemeral=True)
        print "DONE CREATING"

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
    import logging
    logging.basicConfig()

    zh = "localhost:41760"
    #zoo = KazooClient(hosts=zh)
    #zoo.start()
    c = Connection(zh)
    #print "CHILDREN:",zoo.get_children("/")
    c.close()
    #print "CHILDREN:",zoo.get_children("/")