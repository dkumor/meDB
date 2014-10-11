

import uuid

"""
The permissions data structure is as follows:

_id: the sid
secret: The "password" which gives access to the sid

read: [] #Array. Can contain either: 
        1) "db" - can read contents of database from any sid
        2) sid - Can read data from the given sid
write: T/F : Whether or not allowed to write to the database
"""

class perm(object):
    #The permissions for each object being accessed are stored in memory in the form of this object
    #The object modifies the database when things are set/unset
    def __init__(self,data,db):
        self.db = db
        #First, let's set the sid
        self.__id  = data["_id"]
        self.__secret = data["secret"]
        
        #Read the permissions
        self.__readall = False
        self.__read = {}
        
        #Get the permissions in a dictionary for fast access
        for p in data["read"]:
            if (p=="db"):
                self.__readall = True
            else:
                self.__read[p] = True
                
        self.__write = data["write"]
        
        #All is initialized. Shit's cool
    
    def getWrite(self):
        return self.__write
    def setWrite(self,s):
        if (s!= self.__write):
            self.db.update({"_id":self.__id},{"$set":{"write": s}},upsert=False)
            self.__write = s
    
    write = property(getWrite,setWrite,doc="Whether or not the accessor has write permissions")
    
    def read(self,sid,newval=None):
        if (newval==None):
            if (self.__readall): return True
            return (sid in self.__read)
            
        elif (newval == True):
            #Should we update it at all?
            if not sid in self.__read:
                self.__read[sid] = True
                self.db.update({"_id":self.__id},{"$addToSet":{"read": sid}},upsert=False)
            
            pass
        else: #newval == false
            if (sid in self.__read):
                del self.__read[sid]
                
                self.db.update({"_id":self.__id},{"$pull":{"read": sid}})

    def getSecret(self):
        return self.__secret
    def setSecret(self,s):
        self.db.update({"_id":self.__id},{"$set":{"secret": s}},upsert=False)
        self.__secret = s
        
    secret = property(getSecret,setSecret)
    
    def delete(self):
        #Deletes the entire record
        self.db.remove({"_id": self.__id})
    
    

class Permissions(object):
    """
        Given a mongoDB database object, opens the collection 
    """
    def __init__(self,db,name="permissions"):
        self.p = db[name]
        
    def __call__(self,sid,secret):
        #Given sid and secret, returns the permissions object
        res = self.p.find_one({"_id": sid,"secret": secret})4
        if (res!=None):
            return perm(res,self.p)
        return None
        
    def get (self,sid):
        #Gets permissions based on sid
        res = self.p.find_one({"_id": sid})
        if (res!=None):
            return perm(res)
        return None
    def create(self,sid,secret,read = [],write = False):
        

if (__name__=="__main__"):
