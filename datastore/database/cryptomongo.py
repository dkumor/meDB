import os

import mongo
from container import DatabaseContainer

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MongoContainer")

class MongoContainer(DatabaseContainer):
    """
    Opens a container and starts a mongoDB database within
    """
    smallSize = 5000
    def __init__(self,dbid):
        DatabaseContainer.__init__(self,dbid)
        self.isopener = False

        self.connection = None
        self.cur = None

        self.dbfolder = os.path.join(self.decloc,"db")
        self.portfile = os.path.join(self.decloc,"port")

    def checkSize(self):
        dbsize = int(os.path.getsize(self.datafile)*1e-6)
        if (dbsize < 1000):
            raise Exception("Database file too small to hold database!")
        return (dbsize < self.smallSize)

    def create(self,password,size=10000):
        logger.info("Create database: %s (%iM)",self.dbfolder,size)
        if (size < 1000):
            raise Exception("Given size too small for database")

        DatabaseContainer.create(self,password,size)
        self.isopener = True

        #The container is now mounted, so we create the database folder (db)
        os.mkdir(self.dbfolder)

        try:
            self.connection = mongo.Connection(self.dbfolder,self.checkSize())
        except:
            DatabaseContainer.close(self)
            raise

        self.cur = self.connection.cursor()

        #Write the port number to a file
        with open(self.portfile,"w") as f:
            f.write(str(self.connection.port))


    def open(self,password=None):
        if (self.isopen()):
            logger.info("Open (already open): %s",self.dbfolder)
            portnm = 0
            #Read the port number from the file
            with open(self.portfile,"r") as f:
                portnum = int(f.read())
            if (portnum < 27017):
                raise Exception("Read portnum that is in weird range")

            self.cur = mongo.getCursor(portnum)
        else:
            logger.info("Open (decrypt): %s",self.dbfolder)
            DatabaseContainer.open(self,password)
            self.isopener = True

            try:
                self.connection = mongo.Connection(self.dbfolder,self.checkSize())
            except:
                DatabaseContainer.close(self)
                raise

            self.cur = self.connection.cursor()

            #Write the port number to a file
            with open(self.portfile,"w") as f:
                f.write(str(self.connection.port))

    def cursor(self):
        return self.cur


    def close(self):
        if (self.connection!=None):
            self.connection.close()
        if (self.isopener):
            DatabaseContainer.close(self)

    def forceClose(self):
        if (self.connection!=None):
            self.connection.close()
        DatabaseContainer.close(self)

    def panic(self):
        if (self.connection!=None):
            self.connection.close()
        DatabaseContainer.panic(self)

if (__name__=="__main__"):
    MongoContainer.fileLocation = "./test_db"
    MongoContainer.tmpLocation = "./test_mnt"

    import shutil
    import time

    pwd = "testpassword"

    if (os.path.exists(MongoContainer.fileLocation)):
        shutil.rmtree(MongoContainer.fileLocation)
    if (os.path.exists(MongoContainer.tmpLocation)):
        shutil.rmtree(MongoContainer.tmpLocation)

    c = MongoContainer("testDatabase")

    print "Checking preliminary"
    assert not c.isopen()
    assert not c.exists()

    print "Creating..."
    t = time.time()
    c.create(pwd,1000)
    createTime = time.time()-t

    assert c.exists()
    assert c.isopen()

    db = c.cursor().db.input
    db.insert({"hi": "hello","wee":"waa"})


    print "Closing..."
    t=time.time()
    c.close()
    closeTime = time.time()-t

    assert not c.isopen()
    assert c.exists()
    print "Opening"
    t = time.time()
    c.open(pwd)
    openTime = time.time()-t

    assert c.isopen()

    db = c.cursor().db.input
    dta = db.find_one({"hi":"hello"})

    print "Closing"
    t=time.time()
    c.close()
    closeTime2 = time.time()-t

    print "Cleaning up"
    shutil.rmtree(MongoContainer.fileLocation)
    shutil.rmtree(MongoContainer.tmpLocation)

    assert not c.exists()
    assert dta["wee"]=="waa"
    print dta
    print "Create Time:",createTime
    print "Open Time:",openTime
    print "Close Time",closeTime,closeTime2
