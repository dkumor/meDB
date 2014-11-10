"""
The metaobject is basically an object that allows changes to a mongoDB object as if it were just
a dict in python. It allows access of values, and it also allows writing only certain values back to
the database.
"""

class MongoObject(object):
    def __init__(self,database,find,get="",data=None,autocommit = True):
        #The data is the current state of the object - if it was already read

        #Actual database stuff
        self.db = database
        self.find = find
        self.get = get

        #The temp holder of changes to the dict
        self.cache = {}  
        self.autocommit = autocommit

        self.data = data
        if (data is None):
            self.data = {}
            self.reload()   #Loads the object into memory

    def __getitem__(self,idx):
        #Return the newest values (including cached and uncommitted changes)
        if (idx in self.cache):
            return self.cache[idx]
        return self.data[idx]

    def __setitem__(self,idx,val):
        #Sets the given item to the correct value
        self.cache[idx] = val
        if (self.autocommit == True):
            self.commit()

    def reload(self):
        #Reloads the object's state from database
        self.revert()
        if (self.get==""):
            self.data = self.db.find_one(self.find)
        else:
            self.data = self.db.find_one(self.find,{self.get: True})
            del self.data["_id"]    #Deletes the default "_id" arg, so that only the wanted key remains
            self.data = self.data[self.data.keys()[0]]
        print "GET:",self.data

    def revert(self):
        #Clears the cache of changes, and reverts to original data
        self.cache = {}
    
    def commit(self):
        #Commits the changes made to the object, and clears the cache
        insertdict = {}
        g = ""
        if (len(self.get)>=1):
            g = self.get+"."
        for k in self.cache:
            self.data[k] = self.cache[k]
            insertdict[g+k] = self.cache[k]

        self.cache = {}

        self.db.update(self.find,{"$set": insertdict})

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