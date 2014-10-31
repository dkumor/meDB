import os

import mongo
from container import DatabaseContainer

class MongoContainer(DatabaseContainer):
    """
    Opens a container and starts a mongoDB database within
    """
    logger = None #The logger is initially set to None, but it must exist before init is called
    smallSize = 5000
    def __init__(self,dbid):
        if (self.logger is None):
            raise Exception("Logger is not set")

        DatabaseContainer.__init__(self,dbid)

        self.connection = None
        self.cur = None

        self.dbfolder = os.path.join(self.decloc,"db")

    def checkSize(self):
        dbsize = int(os.path.getsize(self.datafile)*1e-6)
        if (dbsize < 1000):
            raise Exception("Database file too small to hold database!")
        return (dbsize < self.smallSize)

    def create(self,password,size=10000):
        self.logger.info("Create database: %s (%iM)",self.dbfolder,size)
        if (size < 1000):
            raise Exception("Given size too small for database")

        DatabaseContainer.create(self,password,size)

        #The container is now mounted, so we create the database folder (db)
        os.mkdir(self.dbfolder)

        try:
            self.connection = mongo.Connection(self.dbfolder,self.checkSize())
        except:
            DatabaseContainer.close(self)
            raise

        self.cur = self.connection.cursor()

    def open(self,password=None):
        if (self.isopen()):
            self.logger.info("Open (already open): %s",self.dbfolder)
            raise Exception("Tried to open database that is already open")
        else:
            self.logger.info("Open (decrypt): %s",self.dbfolder)
            if (password is None): raise Exception("Container needs password for decryption")
            DatabaseContainer.open(self,password)

            try:
                self.connection = mongo.Connection(self.dbfolder,self.checkSize())
            except:
                DatabaseContainer.close(self)
                raise

            self.cur = self.connection.cursor()

    def cursor(self):
        return self.cur


    def close(self):
        if (self.connection!=None):
            self.connection.close()
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

    import sys
    print os.path.abspath("../../")
    sys.path.append(os.path.abspath("../../"))
    from rootprocess.rootprocess import run
    from rootprocess.client import RootCommander
    from multiprocessing import Process, Pipe
    import logging
    import os
    import cryptfile

    import shutil

    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")

    conf= {
        "mntdir":"./test_mnt",
        "dbdir":"./test_db",
        "user": "cryptomongo"
    }

    logger = logging.getLogger("container")
    logging.basicConfig()
    logger.setLevel(logging.INFO)

    p, child_pipe = Pipe()



    child = Process(target=run,args=(child_pipe,logger,conf,))
    child.start()


    rc = RootCommander(p)
    cryptfile.FileCrypto.rootcommander = rc
    DatabaseContainer.fileLocation = "./test_db"
    DatabaseContainer.mntLocation = "./test_mnt"
    MongoContainer.logger = logger
    print "MONGO",MongoContainer.fileLocation
    import time

    pwd = "testpassword"

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
    shutil.rmtree(MongoContainer.mntLocation)

    assert not c.exists()
    assert dta["wee"]=="waa"
    print dta
    print "Create Time:",createTime
    print "Open Time:",openTime
    print "Close Time",closeTime,closeTime2

    print "Cleaning up"

    p.send("EOF")
    child.join()

    print "Done"
