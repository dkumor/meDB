import requests
import json

from pymongo import MongoClient

class CryptoMongo(object):
    timeout = 180   #3 minutes for the server to open shit n'stuff

    def __init__(self,server="http://127.0.0.1:49200"):
        self.server = server
    def q(self,d):
        r = requests.post(self.server,data=d)
        if (r.status_code!=200):
            return None
        r = json.loads(r.text)
        return r

    """
    Connect - the most important function. Allows to connect to the given database
    """

    def connect(self,name):
        #Connect to an already open database.
        r= self.q({"cmd": "connect","name": name})
        if (r is not None):
            return MongoClient(port=int(r))
        return None

    def ls(self):
        return self.q({"cmd": "ls"})



    """
    The following functions are administrative - they allow control of the databases within the cluster
    """

    def isopen(self,name):
        return self.q({"cmd": "isopen","name":name})

    def exists(self,name):
        return self.q({"cmd": "exists","name":name})

    def create(self,name,password,size=2048):
        #Create an entirely new database container
        r= self.q({"cmd": "create","size":size,"name": name,"pass": password})
        if (r is not None):
            return MongoClient(port=int(r))
        return None
    def open(self,name,password):
        #Opens an existing database container
        r = self.q({"cmd": "open","name": name,"pass":password})
        if (r is not None):
            return MongoClient(port=int(r))
        return None
        
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
        self.q({"cmd": "panicall"})




if (__name__=="__main__"):
    import time
    print "Started"
    t = time.time()
    c = CryptoMongo()
    assert len(c.ls())==0
    assert c.exists("hello") == False
    assert c.isopen("hello") == False

    assert c.connect("hello") == None

    db = c.create("hello","password",2048).db.input
    db.insert({"hi": "hello","wee":"waa"})
    print "INSERT"
    assert c.exists("hello") == True
    assert c.isopen("hello") == True

    assert c.connect("hello") is not None

    assert len(c.ls())==1
    assert c.ls()[0] == "hello"
    print "CLOSE"
    c.close("hello")

    assert c.exists("hello") == True
    assert c.isopen("hello") == False
    assert len(c.ls())==0

    assert c.connect("hello") is None
    print "RECREATE"
    assert c.create("hello","pass",2048) is None

    assert c.isopen("hello") == False

    assert c.open("hello","wrong") == None

    assert c.isopen("hello") == False
    print "OPEN"
    assert c.open("hello","password") is not None

    assert c.connect("hello") is not None

    db = c.connect("hello").db.input
    one = db.find_one({"hi":"hello"})

    assert one["wee"]=="waa"
    print "PANIC"
    c.panic("hello")

    try:
        v = db.find_one({"hi":"hello"})
        print v
        print "FAILED - FIND SUCCEEDED ON CLOSED DB"
        exit(0)
    except:
        pass

    assert c.isopen("hello") == False
    assert c.exists("hello") == True
    assert c.connect("hello") is None

    assert c.open("hello","password") is not None
    assert c.connect("hello") is not None
    print "PANICALL"
    c.panicall()

    assert c.isopen("hello") == False
    assert c.exists("hello") == True
    assert c.connect("hello") is None

    assert c.open("hello","password") is not None
    assert c.connect("hello") is not None
    print "DELETE"
    c.delete("hello")

    assert c.isopen("hello") == False
    assert c.exists("hello") == False


    print "Total time:",time.time()-t
    #c.panicall()
