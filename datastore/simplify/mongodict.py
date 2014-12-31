"""
The metaobject is basically an object that allows changes to a mongoDB object as if it were just
a dict in python. It allows access of values, and it also allows writing only certain values back to
the database.
"""

class MongoObject(object):
    def __init__(self,db,find,get="",data=None, autocommit = True):
        """
            db - link to the collection of the mongoDB database
            find - what query to run in order to get the correct document
            get - the object could be part of a subdocument. How to get it from the database
            data - if the data was already queried, no use in getting data again
        """

        self._db = db
        self._find = find
        self._get = get
        self._data = data

        
        self._cache = {}  

        self.autocommit = autocommit    #Whether or not commit happens on change

        
        if (data is None):
            self.reload()   #Loads the object into memory

    def __getitem__(self,idx):
        #Return the newest values (including cached and uncommitted changes)
        if (idx in self._cache):
            return self._cache[idx]
        if (idx in self._data):
            return self._data[idx]
        return None

    def __setitem__(self,idx,val):
        #Sets the given item to the correct value
        self._cache[idx] = val
        if (self.autocommit == True):
            self.commit()

    def reload(self):
        #Reloads the object's state from database
        self.revert()
        if (self._get==""):
            self._data = self._db.find_one(self._find)
        else:
            self._data = self._db.find_one(self._find,{self._get: True,"_id": False})
            self._data = self._data[self._data.keys()[0]]

    def revert(self):
        #Clears the cache of changes, and reverts to original data
        self._cache = {}
    
    def getChildPath(self,p):
        if (self._get==""):
            return p
        else:
            return self._get+"."+p

    def getChild(self,idx):
        #Gets the child as a mongoObject
        if (self[idx] is not None):
            return MongoObject(self._db,self._find,self.getChildPath(idx),self[idx],self.autocommit)
        return None

    def commit(self):
        #Commits the changes made to the object, and clears the cache
        insertdict = {}
        deletedict = {}
        g = ""
        if (len(self._get)>=1):
            g = self._get+"."
        for k in self._cache:
            if (self._cache[k] is None):
                #We delete the element
                if (k in self._data):
                    del self._data[k]
                deletedict[g+k] = True
            else:
                self._data[k] = self._cache[k]
                insertdict[g+k] = self._cache[k]

        self._cache = {}

        q = {}
        if (len(insertdict)>0):
            q["$set"] = insertdict
        if (len(deletedict)>0):
            q["$unset"] = deletedict
        
        if (len(q)>0):
            self._db.update(self._find,q)

    def delete(self,idx):
        self[idx] = None    #Setting to None deletes
    def contains(self,a):
        if (a in self._cache):
            return (self._cache[a] is not None)
        if (a in self._data):
            return True
        return False
    def __contains__(self,a):
        return self.contains(a)
    def __str__(self):
        return "("+str(self._data)+")["+str(self._cache)+"]"
    def __len__(self):
        return len(self._data)

class RecursiveMongoObject(MongoObject):
    def __init__(self,db,find,get="",data=None, autocommit = True,rerecursion=0):
        MongoObject.__init__(self,db,find,get,data,autocommit)
        self.rerecursion = rerecursion

        self.clearInternalObjects()

    def clearInternalObjects(self):
        #Warning: I am making a very important assumption by caching names:
        #The assumption is that a cached name will actually exist! The reads
        #can be done in parallel, since data about a user is committed to the database in useful
        #chunks, but writes need to all be done from one process
        self._names = {}

    def reload(self):
        MongoObject.reload(self)
        #After reload, the internal objects can be invalid
        self.clearInternalObjects()

    def commit(self):
        MongoObject.commit(self)
        for name in self._names:
            self._names[name].commit()

    def __getitem__(self,i):
        return self.getChild(i,self.rerecursion)
    def __setitem__(self,i,v):
        MongoObject.__setitem__(self,i,v)
        if (i in self._names):
            del self._names[i]  #Setting the object should reset the cached mongoObject

    def getChild(self,i,recursion=0,specialObject=None):
        #Gets the child as a mongoObject, rather than recursiveMongo object
        if (MongoObject.__getitem__(self,i) is None):
            return None
        if (i not in self._names):
            if (specialObject is not None):
                #Allows it to simply use a special child. Not sure /why/ yet, but it sounds useful
                if (recursion > 0):
                    self._names[i] = specialObject(self._db,self._find,self.getChildPath(i),MongoObject.__getitem__(self,i),self.autocommit,recursion-1)
                else:
                    self._names[i] = specialObject(self._db,self._find,self.getChildPath(i),MongoObject.__getitem__(self,i),self.autocommit)
            elif (recursion > 0):
                self._names[i] = RecursiveMongoObject(self._db,self._find,self.getChildPath(i),MongoObject.__getitem__(self,i),self.autocommit,recursion-1)
            else:
                self._names[i] = MongoObject(self._db,self._find,self.getChildPath(i),MongoObject.__getitem__(self,i),self.autocommit)
        return self._names[i]

if (__name__=="__main__"):
    from pymongo import MongoClient


    db = MongoClient().testing.test

    #Clear the database
    db.remove()

    db.insert({"reload":"hi","heh":{"inside":"me"}})


    c = MongoObject(db,{"reload":"hi"},"heh",autocommit=False)

    c["hi"] = 34
    c["hello"] ="wow"

    print db.find_one({"reload": "hi"})

    c.commit()

    

    c["hi"] = "IT WORKS"

    assert c["hi"] == "IT WORKS"

    print db.find_one({"reload": "hi"})
    c.commit()
    print db.find_one({"reload": "hi"})
    #Clear
    db.remove()