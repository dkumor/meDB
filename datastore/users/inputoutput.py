#Allows for creation of new inputs and outputs

from mongoobject import MongoObject

import uuid
from bson.objectid import ObjectId

class IO_io(MongoObject):
    """
    Extremely simplified MongoObject - it is really jsut a wrapper that gives the next level
    of mongoObjects
    """
    def __init__(self,db,find,get="",data=None, autocommit = True):
        MongoObject.__init__(self,db,find,get,data,autocommit)

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
        if (MongoObject.__getitem__(self,i) is None):
            return None
        if (i not in self._names):
            self._names[i] = MongoObject(self._db,self._find,self.getChildPath(i),MongoObject.__getitem__(self,i),self.autocommit)
        return self._names[i]

class IO(MongoObject):

    @staticmethod
    def create():
        return {
            "_id": ObjectId(uuid.uuid4().hex[:24]),
            "meta": {}, #Metadata of the entire io
            "io": {}    #The document containing all registers
            }

    #Given an existing IO object, manages everything about it
    def __init__(self,db,find,get="",data=None, autocommit = True):
        MongoObject.__init__(self,db,find,get,data,autocommit)

        #Make the internal objects exist
        self.clearInternalObjects()

    def clearInternalObjects(self):
        self._meta = None   #The metadata object for the io
        self._io = None   #The part object for the io

    def reload(self):
        MongoObject.reload(self)
        #After reload, the internal objects can be invalid
        self.clearInternalObjects()
    def commit(self):
        MongoObject.commit(self)
        if (self._meta is not None):
            self._meta.commit()
        if (self._io is not None):
            self._io.commit()

    #Allows for modification of the metadata associated with an io
    def getMeta(self):
        if (self._meta is None):
            self._meta = self.getChild("meta")
        return self._meta
    def setMeta(self,m):
        self["meta"] = m
        self._meta = None   #The meta object is no longer valid
        #WARNING io is not committed - getio might fail miserably if get 
        #   is done after set, and before commit

    meta = property(getMeta,setMeta)

    def getIo(self):
        if (self._io is None):
            self._io = IO_io(self._db,self._find,self.getChildPath("io"),self["io"],self.autocommit)
        return self._io
    def setIo(self,i):
        self["io"] = i
        self._io = None
        #WARNING io is not committed - getio might fail miserably if get 
        #   is done after set, and before commit

    io = property(getIo,setIo)



    
if (__name__=="__main__"):
    from pymongo import MongoClient

    db = MongoClient().testing.test

    #Clear the database
    db.remove()
    v = IO.create()
    val = v["_id"]
    db.insert(v)
    v = IO(db,{"_id": val},autocommit=False)
    assert str(v.meta)=="({})[{}]"
    v.meta = {"word":"up","gg":"game"}
    #WARNING: if autocommit is off, need to manually commit after setting meta
    v.commit()
    assert str(v.meta)=="({'gg': 'game', 'word': 'up'})[{}]"
    v.meta["hi"]=5
    v.meta["word"] = "down"
    assert str(v.meta) == "({'gg': 'game', 'word': 'up'})[{'hi': 5, 'word': 'down'}]"
    v.commit()
    
    assert str(v.meta) == "({'gg': 'game', 'hi': 5, 'word': 'down'})[{}]"
    assert str(db.find_one()["meta"]) == "{u'gg': u'game', u'hi': 5, u'word': u'down'}"


    assert len(v.io)==0
    v.io["light1"]={"type": "bool"}
    v.io["light2"]={"type": "bool"}
    v.io["light3"]={"type": "bool"}
    assert len(v.io)==0
    v.commit()

    assert len(v.io)==3
    assert "light2" in v.io
    assert not "light8" in v.io

    v.io.delete("light2")
    v.io.commit()

    assert not "light2" in v.io
    assert str(db.find_one()["io"]) == "{u'light3': {u'type': u'bool'}, u'light1': {u'type': u'bool'}}"

    assert v.io["light1"]["type"] == "bool"
    v.io["light1"]["type"] = "int"
    assert str(v.io["light1"]) == "({'type': 'bool'})[{'type': 'int'}]"
    v.io.commit()
    assert str(v.io["light1"]) == "({'type': 'int'})[{}]"

