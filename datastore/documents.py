import pymongo
import time
from bson.objectid import ObjectId

"""
The Documents data structure is as follows:

_id: randomly renerated identifier
uid: the id of the owner
data: {} The structure which contains data formatted in json
time: timestamp
"""

class Documents(object):
    def __init__(self,db,dbname="documents"):
        self.c = db[dbname]
        #Make sure that an index exists
        self.c.create_index([("uid",pymongo.DESCENDING),("time",pymongo.DESCENDING)])

    def add(self,uid,data,timestamp=None):
        #Adds the given data structure to the database
        if (timestamp is None):
            timestamp = time.time()

        return self.c.insert({"uid": ObjectId(uid),"data": data,"time": timestamp})

    def remove(self,oid):
        #Removes the record with the given oid
        self.c.remove({"_id": ObjectId(oid)})

    def removeuid(self,uid):
        #Removes all records of the given UID
        self.c.remove({"uid": ObjectId(uid)})

    def get(self,uid=None,key=None,starttime=None,endtime=None,oid=None):
        #Get a cursor to the elements given the restrictions
        v = {}

        if (uid!=None):
            ids = {"$in":uid}
            if (isinstance(uid,ObjectId)): #Allows to search by one objectId
                ids = uid
            v["uid"] = ids

        t = {}
        if (starttime!=None):
            t["$gt"] = starttime
        if (endtime != None):
            t["$lt"] = endtime
        if (len(t.keys())>0):
            v["time"] = t

        if (key!=None):
            if (isinstance(key, basestring)):
                v["data."+key] = {"$exists": True}
            else:
                for i in key:
                    v["data."+i] = {"$exists": True}

        if (oid != None):
            ods = {"$in":oid}
            if (isinstance(oid,ObjectId)): #Allows to search by one objectId
                ods = oid
            v["_id"] = ods

        print v
        return self.c.find(v)

    def size(self):
        return self.c.dataSize()
    def count(self):
        return self.c.count()
    def __len__(self):
        return self.count()
    def stats(self):
        return self.c.stats()

if (__name__=="__main__"):
    import shutil
    import os
    import uuid
    from database.mongo import Connection


    testname = "./test_db"


    if (os.path.exists(testname)):
        shutil.rmtree(testname)

    os.mkdir(testname)

    user1 = ObjectId(uuid.uuid4().hex[:24])
    user2 = ObjectId(uuid.uuid4().hex[:24])
    user3 = ObjectId(uuid.uuid4().hex[:24])

    c = Connection(testname)

    d = Documents(c.cursor().db)

    assert len(d)==0
    assert d.get(user1).count() == 0

    i=d.add(user1,{"hi":3,"hello":"hey"})

    assert len(d)==1
    assert d.get(user1).count() == 1
    assert d.get(user2).count() == 0

    assert d.get(user1).next()["data"]["hi"] == 3

    assert d.get(oid=i).count()==1
    assert d.get(key="hello").count()==1
    assert d.get(key="helq").count()==0
    assert d.get(starttime=time.time()).count() == 0
    assert d.get(starttime=time.time()-5).count() == 1  #5 seconds should be enough
    assert d.get([user1,user2,user3],key=["hi","hello"]).count() == 1
    assert d.get([user1,user2,user3],key=["hi","hello","he"]).count() == 0

    c.close()

    shutil.rmtree(testname)

    print "\n\nAll tests completed successfully\n"
