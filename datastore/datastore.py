from database.cryptomongo import MongoContainer
import os

#Imports the structures of the database
from users import Users
from documents import Documents

class DataStore(object):
    def __init__(self,dbid,password=None,size=2048,create=False):
        #Given an ID of the datastore, connect to it.
        #If given a password, open if possible. If given password and size, create if necessary.


        #Opens the container - and creates it if necessary
        self.container = MongoContainer(dbid)
        if not (self.container.exists()):
            if (password != None and create==True):
                self.container.create(password,size)
            else:
                raise Exception("Container does not exist")
        else:
            self.container.open(password)   #If password is NULL, this function opens an existing decrypted container

        #Everything is stored in the "datastore" database
        self.db = self.container.cursor().datastore

        #Initialize the collections
        self.users = Users(self.db)
        self.documents = Documents(self.db)

    #Methods of closing the datastore
    def close(self):
        #Closes the container - and unmounts the encryption if it is the DataStore that decrypted the container.
        self.container.close()
    def encrypt(self):
        #Forces actual clean shutdown of the container, whether or not this object is the creator.
        self.container.forceClose()
    def panic(self):
        #Basically forces immediate unmounting and encrytion - only for emergencies, as can cause data loss
        self.container.panic()



if (__name__=="__main__"):
    #Change the file locations of the container for testing
    MongoContainer.fileLocation = "./test_db"
    MongoContainer.tmpLocation = "./test_mnt"

    dname = "adfsfd"
    dpwd = "password"

    import shutil
    import time

    if (os.path.exists(MongoContainer.fileLocation)):
        shutil.rmtree(MongoContainer.fileLocation)
    if (os.path.exists(MongoContainer.tmpLocation)):
        shutil.rmtree(MongoContainer.tmpLocation)

    d = DataStore(dname,dpwd,create=True)

    d2 = DataStore(dname)

    u = d.users.create(secret="lolz",read=["db",],write=True).id

    assert d2.users(u,"lolz") != None

    d2.close()

    #d should still work
    assert d.users(u,"lolz") != None

    d.close()

    #trying to open buffer that is not decrypted should fail
    err=False
    try:
        d = DataStore(dname)
    except Exception as e:
        print e
        err=True
    assert err==True

    print "\n\nAll tests completed successfully!"
