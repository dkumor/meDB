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
            self._data = self._db.find_one(self._find,{self._get: True})
            del self._data["_id"]    #Deletes the default "_id" arg, so that only the wanted key remains
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
        else: return False
    def __contains__(self,a):
        return self.contains(a)
    def __str__(self):
        return "("+str(self._data)+")["+str(self._cache)+"]"
    def __len__(self):
        return len(self._data)

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