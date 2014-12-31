
from mongoobject import MongoObject,RecursiveMongoObject

class Permission(MongoObject):
    @staticmethod
    def create():
        """
            {
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
        """
        return {
            "r":False,
            "o": False,
            "p": False,
            "s": False,
            "wp": False,
            "ws": False,
            "wr": False,
            "wo": False,
            "d": False,
            }

    def getRead(self):
        return self["r"]
    def setRead(self,i):
        self["r"] = i
    read = property(getRead,setRead)

    def getOutputs(self):
        return self["o"]
    def setOutputs(self,i):
        self["o"] = i
    outputs = property(getOutputs,setOutputs)

    def getWOutputs(self):
        return self["wo"]
    def setWOutputs(self,i):
        self["wo"] = i
    woutputs = property(getWOutputs,setWOutputs)

    def getWInputs(self):
        return self["wr"]
    def setWInputs(self,i):
        self["wr"] = i
    winputs = property(getWInputs,setWInputs)

    def getSecret(self):
        return self["s"]
    def setSecret(self,i):
        self["s"] = i
    secret = property(getSecret,setSecret)

    def getWSecret(self):
        return self["ws"]
    def setWSecret(self,i):
        self["ws"] = i
    wsecret = property(getWSecret,setWSecret)

    def getWPermissions(self):
        return self["wp"]
    def setWPermissions(self,i):
        self["wp"] = i
    wpermissions = property(getWPermissions,setWPermissions)

    def getPermissions(self):
        return self["p"]
    def setPermissions(self,i):
        self["p"] = i
    permissions = property(getPermissions,setPermissions)

    def getDelete(self):
        return self["d"]
    def setDelete(self,i):
        self["d"] = i
    delete = property(getDelete,setDelete)


class Permissions(RecursiveMongoObject):
    def getChild(self,i,rerecursion=0):
        return RecursiveMongoObject.getChild(self,i,0,Permission)

    def create(self,v):
        self[v] = Permission.create()

if (__name__=="__main__"):
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    import uuid

    db = MongoClient().testing.test

    #Clear the database
    db.remove()
    id = ObjectId(uuid.uuid4().hex[:24])
    db.insert({"_id": id})

    p = Permissions(db,{"_id": id},autocommit=False)

    assert len(p) == 1  #The _id adds one

    p.create("hello")
    p.commit()
    p["hello"].read = True
    assert str(p["hello"]) == "({'p': False, 's': False, 'r': False, 'ws': False, 'wr': False, 'wp': False, 'wo': False, 'o': False, 'd': False})[{'r': True}]"
    p.commit()
    assert str(p["hello"]) == "({'p': False, 's': False, 'r': True, 'ws': False, 'wr': False, 'wp': False, 'wo': False, 'o': False, 'd': False})[{}]"


    