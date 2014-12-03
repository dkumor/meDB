
import threading
import time

import rootcommander
from database import cryptfile, container
from database.mongocontainer import MongoContainer


class DatabaseManager(object):
    """
    Stores all mongoDB databases and makes sure that they are all contained correctly
    """
    def __init__(self,rc,dbdir,mntdir):

        #cryptFile actually needs root to use LUKS, so we set its rootcommander
        cryptfile.FileCrypto.rootcommander = rc

        #Containers need to know their mount/database container directories
        container.DatabaseContainer.fileLocation = dbdir
        container.DatabaseContainer.mntLocation = mntdir

        self.databases = {}
        self.d_lock = threading.Lock()

        #Locks the entire manager upon a panic
        self.ispanic = False

    def chkpanic(self):
        if (self.ispanic): raise Exception("Panic mode enabled")

    def registerOrDie(self,dbid):
        #If the database given is not yet open, lock its state as "processing"
        self.chkpanic()
        self.d_lock.acquire()
        if not (dbid in self.databases):
            l = threading.Lock()
            l.acquire()
            self.databases[dbid] = l
            self.d_lock.release()
            return l
        else:
            self.d_lock.release()
            return None

    def waitFor(self,dbid):
        #Wait until the given dbid is available, and then return it
        self.chkpanic()
        self.d_lock.acquire()
        if (dbid in self.databases):
            v = self.databases[dbid]
            if not (isinstance(v,MongoContainer)):
                self.d_lock.release()
                v.acquire()
                v.release()
                return self.waitFor(dbid)
            else:
                #DOES NOT RELEASE THE LOCK - The lock is to be released in user code
                return v
        #DOES NOT RELEASE d-lock
        return None

    def register(self,dbid):
        v = self.waitFor(dbid)
        if (v is not None):
            self.d_lock.release()
            return None #The database already exists
        else:
            l = threading.Lock()
            l.acquire()
            self.databases[dbid] = l
            self.d_lock.release()
            return l

    def unregister(self,dbid):
        v = self.waitFor(dbid)
        if (v is not None):
            l = threading.Lock()
            l.acquire()
            self.databases[dbid] = l
        self.d_lock.release()
        return v

    def delreg(self,dbid):
        #I am assuming that the dbid is currently registered, and is a lock.
        self.d_lock.acquire()
        l = self.databases[dbid]
        del self.databases[dbid]
        l.release()
        self.d_lock.release()

    def addreg(self,dbid,elem):
        #Adds the given element to the registry - again, assume that the dbid is registered as processing
        #   and is currently a lock
        self.d_lock.acquire()
        l = self.databases[dbid]
        self.databases[dbid] = elem
        l.release()
        self.d_lock.release()

    def connect(self,dbid):
        db = self.waitFor(dbid)
        self.d_lock.release()   #We don't need to keep the lock
        if (db is not None):
            #get the port number for the database
            return db.port()
        return None


    def open(self,dbid,password):
        self.chkpanic()

        if (self.register(dbid)):
            c = MongoContainer(dbid)
            try:
                c.open(password)
            except:
                self.delreg(dbid)
                raise
            self.addreg(dbid,c)
            return c.port()
        #If already open, just connect to it
        return self.connect(dbid)



    def close(self,dbid):
        v = self.unregister(dbid)
        if (v is not None):
            v.close()
        self.delreg(dbid)

    def closeall(self):
        self.ispanic = True #The ispanic variable stops all new connectinos while closing stuff
        self.d_lock.acquire()
        for k in self.databases.keys():
            if (isinstance(self.databases[k],MongoContainer)):
                self.databases[k].close()
                del self.databases[k]
        self.d_lock.release()
        if (len(self.databases)>0):
            time.sleep(0.5) #Let other things get rid of their locks
            self.closeall()
        self.ispanic = False

    def create(self,dbid,password,size=2048):
        self.chkpanic()

        if (self.register(dbid)):
            c = MongoContainer(dbid)
            try:
                c.create(password,size)
            except:
                self.delreg(dbid)
                raise
            self.addreg(dbid,c)
            return c.port()
        #If already open, just connect to it
        return self.connect(dbid)

    def delete(self,dbid):
        v = self.unregister(dbid)
        if (v is not None):
            v.delete()
        self.delreg(dbid)


    def panic(self,dbid):
        v = self.unregister(dbid)
        if (v is not None):
            v.panic()
        self.delreg(dbid)

    def panicall(self):
        self.ispanic = True

        #Panic all skips all the BS, and goes right to the crypto controller. We're in a hurry.
        cryptfile.FileCrypto.panicall()

        #Next, clear the "open" dict
        self.d_lock.acquire()
        #Make sure we free all locks
        for k in self.databases.keys():
            if not (isinstance(self.databases[k],MongoContainer)):
                self.databases[k].release()

        self.databases = {}
        self.d_lock.release()
        self.ispanic = False

    def ls(self):
        #Lists currently open databases
        self.d_lock.acquire()
        result = self.databases.keys()
        self.d_lock.release()
        return result

    def exists(self,dbid):
        return MongoContainer(dbid).exists()
    def isopen(self,dbid):
        return MongoContainer(dbid).isopen()


if (__name__=="__main__"):
    import sys
    import os
    sys.path.append(os.path.abspath("../"))
    from rootprocess.rootprocess import run
    from rootcommander import RootCommander
    from multiprocessing import Process, Pipe
    import logging



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

    pype, child_pipe = Pipe()



    child = Process(target=run,args=(child_pipe,logger,conf,))
    child.start()

    rc = RootCommander(pype)

    #Okay, create the Database manager here
    db = DatabaseManager(rc,"./test_db","./test_mnt")

    assert db.exists("lol")==False
    assert db.isopen("lol")==False
    assert len(db.ls())==0


    def createfnc():
        print "CREATING LOL"
        p = db.create("lol","password",2048)
        print "DONE CREATING LOL"
    def openfnc():
        print "OPENINGLOL"
        p = db.connect("lol")
        print "DONE OPENING LOL"
        if (p is None):
            print "TEST FAILEDDDDDDD"
        print "Test success openfnc"
    threading.Thread(target=createfnc).start()
    threading.Thread(target=openfnc).start()

    time.sleep(0.1)
    p = db.connect("lol")
    print "DONE OPENING LOL - in main thread"
    assert db.exists("lol")
    assert db.isopen("lol")
    assert db.ls()[0]=="lol"
    db.close("lol")

    assert db.exists("lol")
    assert db.isopen("lol")==False

    assert db.connect("lol") is None

    try:
        db.open("lol","pwd")
        print "FAILED - WRONG PASSWORD ACCEPTED"
        exit(0)
    except:
        pass
    print "AT OPEN of lol again"
    p = db.open("lol","password")
    assert db.isopen("lol")
    p2 = db.create("lol2","password2",2048)
    assert db.isopen("lol2")

    db.closeall()

    assert db.isopen("lol")==False
    assert db.isopen("lol2")==False
    assert db.exists("lol")
    assert db.exists("lol2")

    def openlol():
        print "OPENING LOL"
        p = db.open("lol","password")
        if (p is None):
            print "TEST FAILEDDDDDDD1"
        print "DONE OPENING LOL"
    def openlol2():
        print "OPENING LOL2"
        p = db.open("lol2","password2")
        print "DONE OPENING LOL2"
        if (p is None):
            print "TEST FAILEDDDDDDD2"

    threading.Thread(target=openlol).start()
    threading.Thread(target=openlol2).start()

    p1 = db.connect("lol")
    p2 = db.connect("lol2")


    assert p1 is not None
    assert p2 is not None

    db.panicall()

    assert db.isopen("lol")==False
    assert db.isopen("lol2")==False

    threading.Thread(target=openlol).start()
    threading.Thread(target=openlol2).start()


    p1 = db.connect("lol")
    p2 = db.connect("lol2")


    assert p1 is not None
    assert p2 is not None

    db.delete("lol2")
    assert db.exists("lol2")==False

    db.closeall()

    print "Cleaning up"

    pype.send("EOF")
    child.join()

    shutil.rmtree(MongoContainer.fileLocation)
    shutil.rmtree(MongoContainer.mntLocation)

    print "Done"
