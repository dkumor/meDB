

import uuid
from bson.objectid import ObjectId
"""
The user data structure is as follows:

_id: the uid
secret: The "password" which gives access to the uid

read: [] #Array. Can contain either:
        1) "db" - can read contents of database from any uid
        2) uid - Can read data from the given uid
write: T/F : Whether or not allowed to write to the database

inputs: The inputs to the database that the uid registers. In general, inputs do not need to be registered, and can be
        of any type. A registered input is constrained to within the registered type/range. It allows analysis
        algorithms to normalize and process the data. Registering inputs also allows easy finding of the most common inputs
        {
            inputname: {metadata}
        }
"""

class usr(object):
    #The user info for each object being accessed are stored in memory in the form of this object
    #The object modifies the database when things are set/unset

    #NOTE: The object does NOT query the database for checking things. It caches all the data in memory.
    #   the object needs to be reloaded for changes in the database not initiated through this object to be seen.
    def __init__(self,data,db):
        self.db = db
        #First, let's set the uid
        self.__id  = data["_id"]
        self.__secret = data["secret"]

        #Read the permissions
        self.__read = data["read"]
        self.__readall = ("db" in self.__read)

        #List of sids shouldn't include "db"
        if (self.__readall):
            self.__read.remove("db")

        self.__write = data["write"]

        self.__inputs = data["inputs"]

        #All is initialized. Shit's cool

    def getWrite(self):
        return self.__write
    def setWrite(self,s):
        if (s!= self.__write):
            self.db.update({"_id":self.__id},{"$set":{"write": s}},upsert=False)
            self.__write = s

    write = property(getWrite,setWrite,doc="Whether or not the accessor has write permissions")

    def read(self,uid,newval=None):
        if (newval==None):
            if (self.__readall): return True
            return (uid in self.__read)

        elif (newval == True and not (uid in self.__read)):
            self.__read.append(uid)
            self.db.update({"_id":self.__id},{"$addToSet":{"read": uid}},upsert=False)

        elif (newval ==False): #newval == false
            if (uid in self.__read):
                self.__read.remove(uid)

            self.db.update({"_id":self.__id},{"$pull":{"read": uid}})

    def readlist(self):
        return self.__read

    def getReadall(self):
        return self.__readall
    def setReadall(self,v):
        self.__readall = v
        if (v==True):
            self.db.update({"_id":self.__id},{"$addToSet":{"read": "db"}},upsert=False)
        else:
            self.db.update({"_id":self.__id},{"$pull":{"read": "db"}})

    readall = property(getReadall,setReadall)

    def getSecret(self):
        return self.__secret
    def setSecret(self,s):
        self.db.update({"_id":self.__id},{"$set":{"secret": s}},upsert=False)
        self.__secret = s

    secret = property(getSecret,setSecret)

    def getID(self):
        return self.__id

    id = property(getID)

    #Functions for manipulating input - these are quite brutal in the way they work.
    #The goal is to create functions which will make very basic modifications possible
    #There should be a further class which wraps the inputs.

    def addInput(self,name,meta={}):
        #Adds an input with the given name and given metadata to the register
        self.db.update({"_id":self.__id},{"$set": {"inputs."+name: meta}},upsert=False)
        self.__inputs[name] = meta

    def remInput(self,name):
        #Removes the input with the given name from the register
        if (name in self.__inputs):
            self.db.update({"_id":self.__id},{"$unset": {"inputs."+name: ""}},upsert=False)
            del self.__inputs[name]

    def setInput(self,name,meta):
        #Sets the input with the given name with meta
        if (name in self.__inputs):
            self.addInput(name,meta)
        else: raise Exception("Could not find the given input")

    def getInput(self,name):
        #Gets the input with the given name. Returns None if no input exists
        if (name in self.__inputs):
            return self.__inputs[name]
        return None

    def inputlist(self):
        #Returns a list of all registered input names
        return self.__inputs.keys()

    def delete(self):
        #Deletes the entire record
        self.db.remove({"_id": self.__id})

    def __eq__(self,x):
        return str(self) == str(x)

    def __str__(self):
        return str(self.id)

class Users(object):
    """
        Given a mongoDB database object, opens the collection
    """
    def __init__(self,db,name="users"):
        self.p = db[name]

    def __call__(self,uid,secret):
        if not ObjectId.is_valid(uid): return None
        #Given uid and secret, returns the user object
        res = self.p.find_one({"_id": ObjectId(uid),"secret": secret})
        if (res!=None):
            return usr(res,self.p)
        return None

    def get(self,uid):
        if not ObjectId.is_valid(uid): return None
        #Gets user based on uid
        res = self.p.find_one({"_id": ObjectId(uid)})
        if (res!=None):
            return usr(res,self.p)
        return None
    def create(self,uid=None,secret=None,read = [],write = False):
        if (uid==None):
            uid = uuid.uuid4().hex[:24]
        else:
            if not ObjectId.is_valid(uid): return None
        if (secret==None):
            secret = uuid.uuid4().hex
        if (read == True):
            read=["db"]
        r = self.p.insert({"_id": ObjectId(uid),"secret": secret,"read": read,"write": write,"inputs":{}})
        return usr(self.p.find_one({"_id": r}),self.p)



if (__name__=="__main__"):
    import shutil
    import os
    from database.mongo import Connection

    testname = "./test_db"
    if (os.path.exists(testname)):
        shutil.rmtree(testname)

    os.mkdir(testname)
    c = Connection(testname)

    p = Users(c.cursor().db)

    assert p(uuid.uuid4().hex[:24],"fdfsfsd")==None
    assert p.get(uuid.uuid4().hex[:24])==None

    e = p.create(read=True,write=False)

    f = p.get(e.id)

    assert e==f

    assert f.write == False
    assert f.read("safdfsad")==True

    assert f.secret == e.secret
    f.secret = "hlop"
    assert f.secret == "hlop"
    assert f.readall == True

    f.readall = False

    assert f.readall ==False
    assert f.read("safdfsad")==False
    f.read("aardvark",True)
    f.read("trolo",True)
    assert f.read("aardvark")==True

    assert len(f.readlist())==2
    assert "aardvark" in f.readlist()
    assert "trolo" in f.readlist()

    f.write = True
    assert f.write==True

    #Now test the inputs
    assert len(f.inputlist())==0

    assert f.getInput("hi")==None

    f.addInput("hello")
    f.addInput("world",{"gg":4,"ho": ["fg",33]})
    f.addInput("dude",{"foo":"bar"})

    assert len(f.inputlist())==3
    assert f.getInput("hello")!=None
    assert f.getInput("world")["ho"][1]==33
    assert f.getInput("dude")["foo"]=="bar"

    f.setInput("dude",{"gram":3})

    assert not ("foo" in f.getInput("dude"))
    assert f.getInput("dude")["gram"]==3

    f.remInput("dude")

    assert f.getInput("dude") == None

    g = p(f.id,f.secret)

    assert f == g
    assert g.secret == "hlop"
    assert g.readall == False
    assert g.write == True
    assert g.read("safdfsad")==False
    assert g.read("aardvark")==True
    assert g.read("trolo") ==True
    g.read("trolo",False)
    assert g.read("trolo") == False

    assert len(g.inputlist())==2
    assert g.getInput("hello")!=None
    assert g.getInput("world")["ho"][1]==33
    assert g.getInput("dude")==None

    g.addInput("ra",{"men":"yum"})

    assert g.getInput("ra")["men"]=="yum"

    i = f.id
    c.close()
    c = Connection(testname)

    q = Users(c.cursor().db)

    h = q(i,"hlop")
    assert h != None
    assert h.secret == "hlop"
    assert h.readall == False
    assert h.write == True
    assert h.read("safdfsad")==False
    assert h.read("aardvark")==True
    assert h.read("trolo") == False

    assert len(h.inputlist())==3
    assert h.getInput("hello")!=None
    assert h.getInput("world")["ho"][1]==33
    assert h.getInput("dude")==None


    assert q.get(uuid.uuid4().hex[:24])==None
    h.delete()

    assert q.get(i)==None

    assert q.get("hello") == None

    c.close()

    shutil.rmtree(testname)

    print "\n\nAll tests completed successfully\n"
