"""
The mongoobject is basically an object that allows changes to a mongoDB document as if it were just
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

        self.__db = db
        self.__find = find
        self.__get = get
        self.data = data

        self.__cache = {}       #The cache is the list of changes made to the document
        self.__children = {}    #All of the children MongoObjects

        self.autocommit = autocommit    #Whether or not commit happens on change
        
        if (self.data is None):
            self.reload()   #Loads the object into memory

        #Now, check if the data type is array or dict
        self.islist = isinstance(self.data,list)


    def getChild(self,idx):
        if (idx in self.__cache):
            return self.__cache[idx]
        else:
            return self.data[idx]

    def __getitem__(self,idx):
        if (idx in self.__children):
            #If the item already has a child object, return that
            return self.__children[idx]
        elif (idx in self.__cache):
            #If a new change is cached at this level, return the change (since the change is not yet
            #   committed to mongoDB, the object itself can be edited without problems)
            return self.__cache[idx]   
        
        #We check the value differently depending on whether it is list or dict
        tval = None
        if (self.islist):
            tval = (idx < len(self.data))
        else:
            tval = (idx in self.data)
         
        if (tval):
            #Now we get to the interesting part. Each element can be one of 3 things. Either an array
            # or a dict or a value. We handle arrays and dicts, and everything else is returned verbatim
            if (isinstance(self.data[idx],dict) or isinstance(self.data[idx],list)):
                m = MongoObject(self.__db,self.__find,self.getChildPath(idx),self.data[idx],self.autocommit)
                self.__children[idx] = m
                return m
            return self.data[idx]
        return None

    def __setitem__(self,idx,item):
        self.__cache[idx] = item
        if idx in self.__children:
            del self.__children[idx]


    def commit(self):
        pass

    @staticmethod
    def mergequery(a,b):
        #Merge together two dicts so that they form an explicit mongoDB query.
        for i in b:
            if i not in a:
                a[i] = {}
            for j in b[i]:
                a[i][j] = b[i][j]
        return a

    def reload(self):
        #Reloads the object's state from database. Note: This only works for root objects, and objects
        #   which do not have any arrays between them. Otherwise it fails.
        self.revert()
        if (self.__get==""):
            self.data = self.__db.find_one(self.__find)
        else:
            self.data = self.__db.find_one(self.__find,{self.__get: True,"_id": False})
            self.data = self.data[self.data.keys()[0]]

    def revert(self):
        #Clears the cache of changes, and reverts to original data
        self.__cache = {}
        self.__children = {}   
    
    def getChildPath(self,p):
        if (self.__get==""):
            return p
        else:
            return self.__get+"."+str(p)

    def selfquery(self):
        insertdict = {}
        deletedict = {}
        g = ""
        if (len(self.__get)>=1):
            g = self.__get+"."
        for k in self.__cache:
            if (self.__cache[k] is None):
                #We delete the element - only works for dict, not for array
                if (k in self.data):
                    del self.data[k]
                deletedict[g+k] = True
            else:
                
                self.data[k] = self.__cache[k]
                insertdict[g+str(k)] = self.__cache[k]
        q = {}
        if (len(insertdict)>0):
            q["$set"] = insertdict
        if (len(deletedict)>0):
            q["$unset"] = deletedict
        return q

    def query(self):
        q = self.selfquery()
        for i in self.__children:
            q= MongoObject.mergequery(q,self.__children[i].query())
        return q

    def qcommitted(self):
        #This is run when the query was updated. It merges the changes of all the children 
        #into the "full" version.

        for idx in self.__cache:
            self.data[idx] = self.__cache[idx]
        self.__cache = {}

        for i in self.__children:
            self.__children[i].qcommitted()

    
    def commit(self):
        q = self.query()
        self.__db.update(self.__find,q)
        self.qcommitted()

    def contains(self,a):
        if (a in self.__cache):
            return (self.__cache[a] is not None)
        if (a in self.data):
            return True
        return False

    def __contains__(self,a):
        return self.contains(a)
    def __str__(self):
        return "("+str(self.data)+")["+str(self.__cache)+"]"
    def __len__(self):
        return len(self.data)


if (__name__=="__main__"):
    from pymongo import MongoClient


    db = MongoClient().testing.test

    #Clear the database
    db.remove()

    db.insert({"reload":"hi","heh":[1,{"inside":"me"},3,4]})


    c = MongoObject(db,{"reload":"hi"},autocommit=False)
    x = c["heh"]
    z = x[1]
    x[2]="lol"
    z["hai"] = "woah"

    #assert str(c.query()) == "{'$set': {'heh.2.hai': 'woah', 'heh.3': 'lol'}}"
    print c.query()
    c.commit()

    print z
    print db.find_one({"reload":"hi"})
    #Clear
    db.remove()
    