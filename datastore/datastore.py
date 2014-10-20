
import os

#The encrypted mongoDB database container
from database.cryptomongo import MongoContainer

#Imports the structures of the database
from users import Users
from documents import Documents

class DataStore(object):
    def __init__(self,container,dbid,password=None,size=2048,create=False):
        #Given an ID of the datastore, connect to it.
        #If given a password, open if possible. If given password and size, create if necessary.


        #Opens the container - and creates it if necessary
        self.__container = MongoContainer(container)
        if not (self.__container.exists()):
            if (password != None and create==True):
                self.__container.create(password,size)
            else:
                raise Exception("Container does not exist")
        else:
            self.__container.open(password)   #If password is NULL, this function opens an existing decrypted container

        #Make sure that the dbid exists in the database if we are not to create a new one
        if (create==False):
            if not (dbid in self.__container.cursor().database_names()):
                self.close()
                raise Exception("The database ID does not exist")

        #Everything is stored in the database as given by the id
        self.__db = self.__container.cursor()[dbid]

        #Initialize the collections
        self.users = Users(self.__db)
        self.documents = Documents(self.__db)


    #Methods of closing the datastore
    def close(self):
        #Closes the container - and unmounts the encryption if it is the DataStore that decrypted the container.
        self.__container.close()
    def encrypt(self):
        #Forces actual clean shutdown of the container, whether or not this object is the creator.
        self.__container.forceClose()
    def panic(self):
        #Basically forces immediate unmounting and encrytion - only for emergencies, as can cause data loss
        self.__container.panic()

    def delete(self):
        #Removes the entire container. In case you didn't notice, this causes irreversible data loss
        self.__container.delete()

    #Meta-methods
    def stats(self):
        return self.__db.command("dbstats")

    def size(self):
        #Returns the total space that the database takes up
        return self.stats()["storageSize"]

    def getContainer(self):
        return self.__container.name()
    container = property(getContainer)
    def getDb(self):
        return self.__db.name
    database = property(getDb)

    #Whether or not the container exists and is open
    @staticmethod
    def cexists(containername):
        container = MongoContainer(containername)
        return container.exists()
    @staticmethod
    def cisopen(containername):
        container = MongoContainer(containername)
        return container.isopen()
    #Whether or not the given database exists in the given container
    @staticmethod
    def dexists(containername,dbid,password=None):
        container = MongoContainer(containername)
        if (container.exists()):
            container.open(password)
            result = (dbid in container.cursor().database_names())
            container.close()
            return result
        return False
    @staticmethod
    def dlist(containername,password=None):
        container = MongoContainer(containername)
        if (container.exists()):
            container.open(password)
            result = container.cursor().database_names()
            container.close()
            return result
        return None





if (__name__=="__main__"):
    #Change the file locations of the container for testing
    MongoContainer.fileLocation = "./test_db"
    MongoContainer.tmpLocation = "./test_mnt"

    cname = "adfdsf"
    dname = "adfsfd"
    cpwd = "password"

    import shutil
    import time

    if (os.path.exists(MongoContainer.fileLocation)):
        shutil.rmtree(MongoContainer.fileLocation)
    if (os.path.exists(MongoContainer.tmpLocation)):
        shutil.rmtree(MongoContainer.tmpLocation)

    assert DataStore.cexists(cname) == False
    assert DataStore.cisopen(cname) == False

    err=False
    try:
        d = DataStore(cname,dname,cpwd)   #Create should be unset
    except Exception as e:
        print e
        err=True
    assert err==True

    assert DataStore.cexists(cname) == False
    assert DataStore.cisopen(cname) == False

    d = DataStore(cname,dname,cpwd,create=True)

    assert DataStore.cexists(cname) == True
    assert DataStore.cisopen(cname) == True
    assert DataStore.dexists(cname,dname) ==True
    assert DataStore.dexists(cname,"dbshouldntexist") ==False

    d2 = DataStore(cname,dname)

    assert d2.database == dname
    assert d2.container == cname

    u = d.users.create(secret="lolz",read=["db",],write=True).id

    assert d2.users(u,"lolz") != None

    d2.close()

    #d should still work
    assert d.users(u,"lolz") != None

    dstats = d.stats()
    d.close()

    #trying to open buffer that is not decrypted should fail
    err=False
    try:
        d = DataStore(cname,dname)
    except Exception as e:
        print e
        err=True
    assert err==True

    assert DataStore.cexists(cname) == True
    assert DataStore.cisopen(cname) == False
    assert DataStore.dexists(cname,dname,cpwd) ==True
    assert DataStore.dexists(cname,"dbshouldntexist",cpwd) ==False


    print dstats

    print "\n\nAll tests completed successfully!"
