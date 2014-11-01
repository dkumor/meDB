import requests
import json

import pymongo

class CryptoMongo(object):
    timeout = 180   #3 minutes for the server to open shit n'stuff

    def __init__(self,server="http://127.0.0.1:49200"):
        self.server = server
    def q(self,d):
        r = requests.post(self.server,data=d)
        if (r.status_code!=200):
            raise Exception("CryptoMongo command failed")
        r = json.loads(r.text)
        return r

    """
    Connect - the most important function. Allows to connect to the given database
    """

    def connect(self,name):
        #Connect to an already open database.
        r= self.q({"cmd": "connect","name": name})

    """
    The following functions are administrative - they allow control of the databases within the cluster
    """

    def create(self,name,password,size=64):
        #Create an entirely new database container
        r= self.q({"cmd": "create","size":size,"name": name,"pass": password})

    def open(self,name,password):
        #Opens an existing database container
        self.q({"cmd": "open","name": name,"pass":password})

    def close(self,name):
        #Closes the given database container
        self.q({"cmd": "close","name": name})

    def delete(self,name):
        #Deletes the given container. Causes major data loss
        self.q({"cmd": "delete","name":name})

    def panic(self,name):
        #Panics the given database container - possible data loss
        self.q({"cmd": "panic","name":name})

    def panicall(self):
        #Holy shit, things are FUCKED. Panics all open databases.
        self.q({"cmd": "holyfuck"})




if (__name__=="__main__"):
    c = CryptoMongo()
    c.connect("lol")
    c.panicall()
