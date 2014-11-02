
import threading

import rootcommander
from database import cryptfile, container
from database.cryptomongo import MongoContainer


class DatabaseManager(object):
    """
    Stores all mongoDB databases and makes sure that they are all contained correctly
    """
    def __init__(self,rc,dbdir,mntdir):

        #cryptFile actually needs root to use LUKS, so we set its rootcommander
        cryptfile.FileCrypto.rootcommander = rc

        #Containers need to know their mount/database container directories
        container.fileLocation = dbdir
        container.mntLocation = mntdir

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
            if (isinstance(v,threading.Lock)):
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
        if (db is not None):
            #get the port number for the database
            return db.port
        return None


    def open(self,dbid,password):
        self.chkpanic()

        if (self.register(dbid)):
            c = MongoContainer(dbid)
            try:
                c.open(password)
                self.addreg(dbid,c)
                return c.port
            except:
                self.delreg(dbid)
                raise
        #If already open, just connect to it
        return self.connect(dbid)



    def close(self,dbid):
        v = self.unregister(dbid)
        if (v is not None):
            v.close()
        self.delreg(dbid)


    def create(self,dbid,password,size=2048):
        self.chkpanic()

        if (self.register(dbid)):
            c = MongoContainer(dbid)
            try:
                c.create(password,size)
                self.addreg(dbid,c)
                return c.port
            except:
                self.delreg(dbid)
                raise
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
        cryptfile.FileCrypto.panicall()
        self.d_lock.acquire()
        self.databases = {}
        self.d_lock.remove()
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
