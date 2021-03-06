
"""
The User is really a cheap abstraction for inputs and outputs. Rather than have an individual document
for each input and each output, we group them by users. That way, a device that connects has all its properties
associated with one document, and it becomes trivial to modify/check its properties and valid input types.
This also means that users are very, very cheap - each item can be its own user. A heart rate sensor is one user,
and an android app is another - and each user can have multiple inputs and outputs that it defines.

This architecture choice has two benefits: Usually, a sensor defines specific inputs which are somehow related
to each other. This means that correlations and compression of data is more likely to be effective with all the 
inputs of one user.

The user data structure is as follows:

_id: the uid
secret: The "password" which gives access to the uid

perm:   The permissions  of this user with respect to other users
        {
            uid: {
                r: Read data that the user wrote (including things it triggered, and its registered inputs/outputs)
                o: Trigger the user's outputs
                p: Read the user's permissions
                s: Read the user's secret
                wp: Write user's permissions (can only enable permissions it itself has)
                ws: Write the user's secret
                wr: Write the user's registered inputs (ie, allows another user to register inputs)
                wo: Write the user's outputs (ie, allows another user to create/modify outputs)
                d: Can delete user
            }
        }
        1) "db" - sets permissions database-wide (admin has db.<everything>=True)
        2) uid - sets permissions for the given uid

write: T/F : Whether or not allowed to write _data_ to the database
wunreg: If write is true, then:
            -1 : User is not allowed to write unregistered inputs to the database
            <any other number>: The kafka partition number that unregistered inputs are written to.

create: T/F : Whether or not allowed to create user. The new user can only have permissions <= creating user

trigger: [] : Specific IDs of outputs that the user is allowed to trigger. This is similar to the 'o' permission,
        but here, it is not per-user, but rather a specific list of outputs

inputs: The inputs to the database that the uid registers. In general, inputs do not need to be registered, and can be
        of any type. A registered input is constrained to within the registered type/range. It allows analysis
        algorithms to normalize and process the data. Registering inputs also allows easy finding of the most common inputs


outputs: The outputs from the database that the uid registers. Outputs require registration.

Inputs and outputs have data of the following format:

[
    {
        id: The Kafka partition number to which this input/output is written to
        parts: {
            partname: {metadata}
        }
        meta: {metadata}
    }
]


"""

from simplify.mongo import MongoObject
from bson.objectid import ObjectId

#We define a custom exception to handle the actions of the user
class PermissionDenied(Exception):
    pass

class User(object):
    """
    This class exposes the datastore as the specific user sees it. In particular, it maintains and
    enforces all restrictions and permissions for the specific user.
    """

    def __init__(self,conn,usr,secret=None):
        self.connection = conn

        #Try loading the user
        if (secret is not None):
            self.usr = self.ds.users(usr,secret)
        else:
            self.usr = self.ds.users.get(usr)

        #Make sure that the user was extracted
        if (self.usr is None):
            raise PermissionDenied()

    def reload(self):
        #Reload the user from the database
        self.usr = self.ds.users.get(self.usr.id)

    #The single most important function that the user has - write data to the database
    def write(self,data,timestamp=None):
        if not (self.usr.write):
            raise PermissionDenied()
        else:
            self.ds.inputs.add(self.usr.id,data,timestamp)

    #Read data from the database subject to permission clusterf*ck
    def read(self,users=None,attributes=None,starttime=None,endtime=None):
        if (not self.usr.pRead("db")):
            #We don't have unlimited reading access - so make sure we are allowed to read this shit
            if (users is None):
                #users is None, so we want results of all permitted users.
                users = list(self.usr.readset())
            else:
                if (isinstance(users,str)):
                    if not (str(users) in self.usr.readset()):
                        raise PermissionDenied()
                else:
                    users = list(set(users).intersection(self.usr.readset()))
                    if (len(users)==0):
                        raise PermissionDenied()

        return self.ds.inputs.get(users,attributes,starttime,endtime)


    #Registering and unregistering inputs
    def register(self,name,meta = {}):
        if not (self.usr.pWriteInputs(self.usr.id) or self.usr.pWriteInputs("db")):
            raise PermissionDenied()
        else:
            #We don't explicitly run addInput, since we want to keep
            #   any additional metadata that might already exist in the register
            self.usr.input(name,setv=meta)

    def unregister(self,name):
        if not (self.usr.pWriteInputs(self.usr.id) or self.usr.pWriteInputs("db")):
            raise PermissionDenied()
        else:
            self.usr.remInput(name)

    def getinput(self,name):
        if not (self.usr.pRead(self.usr.id) or self.usr.pRead("db")):
            raise PermissionDenied()
        else:
            return self.usr.getInput(name)

    def intersectOutputs(self,outputs):
        #Returns intersection of outputs and the outputs the user is allowed to trigger
        res = []
        for o in outputs:
            #If the output in question o is in the list of trigger outputs
            if (self.usr.output(o)): # or the output's parent is permitted
                res.append(o)

    def mkuser(self,perm={},write=False,create=False,outputs=[]):
        if not (self.usr.create):
            raise PermissionDenied()
        else:
            if not self.usr.write:
                write = False   #If this user can't write, then the child sure as hell can't

import uuid
from bson.objectid import ObjectId

class usr(object):
    #The user info for each object being accessed are stored in memory in the form of this object
    #The object modifies the database when things are set/unset

    #NOTE: The object does NOT query the database for checking things. It caches all the data in memory.
    #   the object needs to be reloaded for changes in the database not initiated through this object to be seen.
    def __init__(self,data,db):
        self.db = db

        self.__id  = data["_id"]
        self.__secret = data["secret"]
        self.__perm = data["perm"]
        self.__write = data["write"]
        self.__wunreg = data["wunreg"]
        self.__create = data["create"]
        self.__trigger = data["trigger"]

        self.__outputs = data["outputs"]
        self.__inputs = data["inputs"]

        #All is initialized. Shit's cool

        self.rset = None #We keep a set of the permitted readers, which is updated when necessary

    #WRITE and CREATE are properties of the user. They can be get/set using usr.write and usr.create
    def getWrite(self):
        return self.__write
    def setWrite(self,s):
        if (s!= self.__write):
            self.db.update({"_id":self.__id},{"$set":{"write": s}},upsert=False)
            self.__write = s
    write = property(getWrite,setWrite,doc="Whether or not the accessor has write permissions")
    def getWriteUnregistered(self):
        return self.__wunreg
    def setWriteUnregistered(self,s):
        if (s!= self.__wunreg):
            self.db.update({"_id":self.__id},{"$set":{"wunreg": s}},upsert=False)
            self.__write = s
    writeunregistered = property(getWriteUnregistered,setWriteUnregistered,doc="Whether or not the accessor is allowed to write unregistered input")

    def getCreate(self):
        return self.__create
    def setCreate(self,s):
        if (s!= self.__create):
            self.db.update({"_id":self.__id},{"$set":{"create": s}},upsert=False)
            self.__create = s
    create = property(getCreate,setCreate,doc="Whether or not accessor allowed to create users")
    #SECRET is also a property of the user
    def getSecret(self):
        return self.__secret
    def setSecret(self,s):
        self.db.update({"_id":self.__id},{"$set":{"secret": s}},upsert=False)
        self.__secret = s
    secret = property(getSecret,setSecret)

    def trigger(self,oid,newval=None):
        #Read and write output-toggling permissions for specific outputs
        hasoutput = (oid in self.__trigger)
        if (newval==None):
            return hasoutput
        elif (newval == True and not hasoutput):
            self.db.update({"_id":self.__id},{"$addToSet":{"trigger": ObjectId(oid)}},upsert=False)
            self.__trigger.append(oid)
        elif (newval == False):
            #Remove it even if it isn't there, just in case it was inserted since we checed
            self.db.update({"_id":self.__id},{"$pull":{"trigger": ObjectId(oid)}})
            if (hasoutput): #We need to check if it exists to remove here
                self.__trigger.remove(oid)

    def triggerlist(self):
        #Returns the list of IDs for the outputs that the user is allowed to toggle
        return self.__trigger

    def __permSet(self,perm,uid,newval):
        #Gets/sets the permission queried in "perm"
        hasid = (uid in self.__perm)
        hasperm = False
        if (hasid): hasperm = (perm in self.__perm[uid])

        if (newval is None):
            #We just get the permissions
            return (hasid and hasperm)
        elif (newval==True):
            if not (hasid):
                #We add both the id and the permission in one go
                self.db.update({"_id":self.__id},{"$set": {"perm."+str(uid): {perm: True}}},upsert=False)
                self.__perm[str(uid)] = {perm: True}
            elif not (hasperm):
                #The ID exists - so we just add the permission
                self.db.update({"_id":self.__id},{"$set": {"perm."+str(uid)+"."+perm: True}},upsert=False)
                self.__perm[str(uid)][perm] = True
        elif (hasid and hasperm):
            #Newval is False - if we are to remove something, this is the place to do it
            if (len(self.__perm[uid])<=1):
                #This permission is the only one for the given ID - so we delete the entire ID
                self.db.update({"_id":self.__id},{"$unset": {"perm."+str(uid): ""}},upsert=False)
                del self.__perm[str(uid)]
            else:
                #There are more permissions for the ID, so just delete this specific one
                self.db.update({"_id":self.__id},{"$unset": {"perm."+str(uid)+"."+perm: ""}},upsert=False)
                del self.__perm[str(uid)][perm]
        #All changes were implemented
        return None



    #Getting and setting permissions for the user with regards to other specific users
    def pRead(self,uid,newval=None):
        if (newval is not None):    #The set of valid readers is no longer valid
            self.rset = None
        return self.__permSet("r",uid,newval)
    def pTrigger(self,uid,newval=None):
        return self.__permSet("o",uid,newval)
    def pReadPerm(self,uid,newval=None):
        return self.__permSet("p",uid,newval)
    def pReadSecret(self,uid,newval=None):
        return self.__permSet("s",uid,newval)
    def pWritePerm(self,uid,newval=None):
        return self.__permSet("wp",uid,newval)
    def pWriteSecret(self,uid,newval=None):
        return self.__permSet("ws",uid,newval)
    def pWriteInputs(self,uid,newval=None):
        return self.__permSet("wr",uid,newval)
    def pWriteOutputs(self,uid,newval=None):
        return self.__permSet("wo",uid,newval)
    def pDelete(self,uid,newval=None):
        return self.__permSet("d",uid,newval)

    def getperm(self,uid):
        hasid = (uid in self.__perm)
        if (hasid):
            return self.__perm[uid]
        return None


    def readset(self):
        if (self.rset is None): #We cache the set of valid readers
            l = []
            for key in self.__perm:
                if ("r" in self.__perm[key]):
                    l.append(key)
            self.rset = set(l)

        return self.rset


    def getID(self):
        return self.__id

    id = property(getID)

    #Functions for manipulating input - these are quite brutal in the way they work.
    #The goal is to create functions which will make very basic modifications possible
    #There should be a further class which wraps the inputs.

    #Functions for modifying input and output registrations.
    def addIO(self,io,parts,meta={}):
        doc = {"id": ObjectId(uuid.uuid4().hex[:24]), "meta": meta, "parts": parts}
        self.db.update({"_id":self.__id},{"$addToSet":{io: doc}},upsert=False)
        return doc
    def remIO(self,io,ioid):
        self.db.update({"_id":self.__id},{"$pull":{io: {"id": ioid}}},upsert=False)
    def clrIO(self,io):
        self.db.update({"_id":self.__id},{"$set": {io: []}},upsert=False)
    def metaIO(self,io,ioid,getv=None,setv=None,delv=None):
        pass


    def addInput(self,name,meta={}):
        #Adds an input with the given name and given metadata to the register
        self.db.update({"_id":self.__id},{"$set": {"inputs."+name: meta}},upsert=False)
        self.__inputs[name] = meta

    def remInput(self,name):
        #Removes the input with the given name from the register
        if (name in self.__inputs):
            self.db.update({"_id":self.__id},{"$unset": {"inputs."+name: ""}},upsert=False)
            del self.__inputs[name]

    def clrInputs(self):
        #Clears the inputs
        self.db.update({"_id":self.__id},{"$set": {"inputs": {}}},upsert=False)
        self.__inputs = {}

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

    #Allows to get/set/delete values in the input's register freely.
    def input(self,name,getv=None,setv=None,delv=None,create=True):
        #Gets/sets the input's value at the given path
        n = self.getInput(name)
        if (n is None): #The input does not exist yet
            if (create==False):
                raise Exception("Could not find the given input")
            else:
                self.addInput(name,setv)
                n = self.getInput(name)
        elif (setv is not None):
            #We set the input
            s = {}
            for key in setv:
                s["inputs."+str(name)+"."+key] = setv[key]
                n[key] = setv[key]
            self.db.update({"_id":self.__id},{"$set": s},upsert=False)

        if (delv is not None):
            s = {}
            for v in delv:
                s["inputs."+str(name)+"."+v] = ""
                if (v in n):
                    del n[v]
            self.db.update({"_id":self.__id},{"$unset": s},upsert=False)

        if (getv is not None):
            #Get the values it asks for
            for key in getv:
                if (key in n):
                    getv[key] = n[key]
                else:
                    getv[key] = None
            return getv
        return None


    def inputlist(self):
        #Returns a list of all registered input names
        return self.__inputs.keys()

    def delete(self):
        #Deletes the entire record for the usert
        self.db.remove({"_id": self.__id})

    def __eq__(self,x):
        return str(self) == str(x)

    def __str__(self):
        return str(self.id)

if (__name__=="__main__"):
    #Change the file locations of the container for testing
    MongoContainer.fileLocation = "./test_db"
    MongoContainer.tmpLocation = "./test_mnt"

    cname = "adfdsf"
    dname = "adfsfd"
    cpwd = "password"

    import shutil
    import time

    if (os.path.exists(MongoContainer.fileLocation)):
        shutil.rmtree(MongoContainer.fileLocation)
    if (os.path.exists(MongoContainer.tmpLocation)):
        shutil.rmtree(MongoContainer.tmpLocation)

    #Open a datastore
    ds = DataStore(cname,dname,cpwd,create = True)

    ds.users.create()


    ds.close()

    print "\n\nAll tests completed successfully!"
