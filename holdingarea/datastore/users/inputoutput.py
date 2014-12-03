#Allows for creation of new inputs and outputs

from mongoobject import RecursiveMongoObject

import uuid
from bson.objectid import ObjectId

class IO(RecursiveMongoObject):

    @staticmethod
    def create():
        return {
            "_id": ObjectId(uuid.uuid4().hex[:24]),
            "meta": {}, #Metadata of the entire io
            "io": {}    #The document containing all registers
            }

    #Allows for modification of the metadata associated with an io
    def getMeta(self):
        return self.getChild("meta")
    def setMeta(self,m):
        self["meta"] = m

    meta = property(getMeta,setMeta)

    def getIo(self):
        return self.getChild("io",1)
    def setIo(self,i):
        self["io"] = i

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

