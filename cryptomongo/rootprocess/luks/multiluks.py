from subprocess32 import call

import threading
import os
import time

import luks

class MultiLuks(object):
    """
        Given a username to mount as, a directory which contains containers,
        and the directory in which to mount containers, allows management of multiple
        luks operations which are coming in asynchronously from multiple python threads
    """
    def __init__(self,user,filedir,mntdir):
        self.mntdir = os.path.abspath(mntdir)
        self.filedir = os.path.abspath(filedir)
        self.user = user

        #The directory in which containers are located must exist
        if not os.path.exists(self.filedir):
            os.mkdir(self.filedir)
            call(["chown","-R",user+":"+user,self.filedir]) #All dirs must belong to user

        #Hold references to the open containers in memory
        self.containers = {}    #A dictionary of open containers
        self.c_lock = threading.Lock()

        self.ispanic = False
    def chkpanic(self):
        if (self.ispanic): raise Exception("Panic mode enabled")
    def getluks(self,container):
        return luks.CryptoLuks(os.path.join(self.filedir,container),os.path.join(self.mntdir,container))
    def registerOrDie(self,container):
        self.chkpanic()
        self.c_lock.acquire()
        if not (container in self.containers):
            self.containers[container] = None
            self.c_lock.release()
            return True
        else:
            self.c_lock.release()
            return False
    def waitFor(self,container):
        self.c_lock.acquire()
        while (container in self.containers and self.containers[container] is None):
            self.c_lock.release()
            time.sleep(0.5)
            self.chkpanic()
            self.c_lock.acquire()
        self.c_lock.release()
    def register(self,container):
        #Waits
        while (True):
            self.waitFor(container)
            self.c_lock.acquire()
            if (container in self.containers and self.containers[container] is not None):
                self.c_lock.release()
                return False    #The container exists - we return False
            self.c_lock.release()
            if (self.registerOrDie(container)):
                return True

    def unregister(self,container):
        self.c_lock.acquire()
        del self.containers[container]
        self.c_lock.release()

    def open(self,container,password):
        self.chkpanic()
        if (self.register(container)):
            #We are registered to open the container
            try:
                cntnr = self.getluks(container)
                cntnr.open(password,owner=self.user)
                self.containers[container] = cntnr
            except Exception, e:
                self.unregister(container)
                raise e #Reraise the error
        else:
            #The container is open as of now
            pass

    def close(self,container):
        self.chkpanic()
        while (True):
            self.waitFor(container)
            self.c_lock.acquire()
            if (container in self.containers and self.containers[container] is not None):
                self.containers[container].close()
                del self.containers[container]
                self.c_lock.release()
                break
            elif not (container in self.containers):    #Release, since DNE
                self.c_lock.release()
                break
            self.c_lock.release()


    def create(self,container,password,size=2048):
        self.chkpanic()
        if not (self.registerOrDie(container)):
            raise Exception("Container already processed.")

        try:
            cntnr = self.getluks(container)
            cntnr.create(password,owner=self.user,fsize = size)

            self.containers[container] = cntnr
        except Exception,e:
            self.unregister(container)
            raise e #Reraise the error

    def panic(self,container):
        self.chkpanic()
        while (True):
            self.waitFor(container)
            self.c_lock.acquire()
            if (container in self.containers and self.containers[container] is not None):
                self.containers[container].panic()
                del self.containers[container]
                self.c_lock.release()
                return
            self.c_lock.release()

    def panicall(self):
        self.ispanic = True     #PANIC MODE ENABLED - nothing new will be created/opened
        while (True):
            self.c_lock.acquire()
            for k in self.containers.keys():
                if (self.containers[k] is not None):
                    self.containers[k].panic()
                    del self.containers[k]
            self.c_lock.release()
            if (len(self.containers)==0):
                break
            #This is bad - one of the containers is currently being created/opened. Sleep a bit and try
            #   panicing it!
            time.sleep(0.5)
        self.ispanic = False    #We are done with panic.

if (__name__=="__main__"):
    import shutil

    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")

    ml = MultiLuks("cryptomongo","./test_db","./test_mnt")

    try:
        ml.open("lala","lol")
        print "OPEN SUCCEEDED - FAIL"
        exit(0)
    except:
        pass
    ml.close("lo")

    ml.create("arr","pass",64)
    try:
        ml.create("arr","pas",64)
        print "CREATE SUCCEEDED - FAIL"
        exit(0)
    except:
        pass

    ml.open("arr","pwd")

    ml.panicall()

    ml.open("arr","pass")

    ml.close("arr")

    try:
        ml.open("arr","pwd")
        print "WRONG PASSWORD OPEN"
        exit(0)
    except:
        pass

    ml.open("arr","pass")

    ml.close("arr")

    def testmultiopen(ml):
        time.sleep(0.2)
        print "OPENING"
        ml.open("arry","pass")
        print "DONEOPEN"
    def testmulticreate(ml):
        print "CREATING"
        ml.create("arry","pass",64)
        print "DONECREATE"

    t1=threading.Thread(target=testmulticreate,args=(ml,))
    t2=threading.Thread(target=testmultiopen,args=(ml,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    ml.panicall()

    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")

    print "DONE"
