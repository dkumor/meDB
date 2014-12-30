import logging
logger = logging.getLogger("connector.client")

from connection import Connection

from pymongo import MongoClient
from kafka import KafkaClient

class ConnectorClient(Connection):
    def __init__(self,zoohost,cname="client",hostname="localhost",rootpath="/connector"):
        Connection.__init__(self,zoohost,cname,hostname,rootpath)

        #Set up clients
        self.kf_client = None
        self.mg_client = None

    def getServerAddress(self,name):
        children = self.zoo.get_children(self.rootpath+"/"+name)
        if (len(children) == 0):
            return None
        host,port,pid = children[0].split(":")
        return host,port

    @property
    def mongo(self):
        if (self.mg_client is None):
            #A mongo connection is not available - create it
            host,port = self.getServerAddress("mongodb")
            self.mg_client = MongoClient(host,int(port))

        return self.mg_client
    @property
    def kafka(self):
        if (self.kf_client is None):
            #A mongo connection is not available - create it
            host,port = self.getServerAddress("kafka")
            self.kf_client = KafkaClient(host+":"+port)

        return self.kf_client

    def close(self):
        if (self.kf_client is not None):
            self.kf_client.close()
        if (self.mg_client is not None):
            self.mg_client.close()

        self.kf_client = None
        self.mg_client = None
        Connection.close(self)
    def __del__(self):
        self.close()