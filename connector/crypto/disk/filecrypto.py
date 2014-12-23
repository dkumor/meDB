"""
RootCommander: Handles all communication with the rootprocess, and makes sure everything is nice and
threadsafe. There can only be ONE rootcommander object. It commands the root - don't want these fuckers
to interfere with each other
"""

import logging
import threading
import random
import sys
import os

from multiprocessing import Process, Pipe
from subprocess32 import call


import usertools
from rootprocess import rootprocess

logger = logging.getLogger("FileCrypto")

class FileCrypto(object):
    def __init__(self,owner,fileDir="./file",mntDir="./mnt",mkusr=False):
        #fileDir: The directory where all cryptoContainers are held
        #mntDir: The EMPTY directory where said containers are mounted
        #owner: The username which will own the containers
        #logger: A logging mechanism
        #mkusr: If owner does not exist, create

        self.owner = owner

        #Make sure we're root
        if (os.getuid() != 0):
            raise Exception("Must be root to start FileCrypto")

        #Makes sure that the owner exists, optionally creating
        if not (usertools.userexists(owner)):
            if (mkusr):
                logger.warn("User %s does not exist, creating."%(owner,))
                usertools.mkusr(owner)
            else: raise Exception("User %s does not exist"%(owner,))


        #Set up file paths
        self.mntdir = os.path.abspath(mntDir)
        self.filedir = os.path.abspath(fileDir)

        #Now, make sure that the fileDir exists
        if not (os.path.isdir(self.filedir)):
            logger.info("Setting up database folder")
            if (os.path.exists(self.filedir)):
                logger.error("'%s' is not a directory!",self.filedir)
                raise Exception(self.filedir+" is not a directory!")
            else:
                os.mkdir(self.filedir,000)
        if not (os.path.isdir(self.mntdir)):
            logger.info("Setting up mountpoints")
            if (os.path.exists(self.mntdir)):
                logger.error("'%s' is not a directory!",self.mntdir)
                raise Exception(self.mntdir+" is not a directory!")
            else:
                #Need whole path at least readable for java to do anything. I HATE java. With a passion.
                #Honestly, "my way of the highway" in everything. No hacking allowed.
                os.mkdir(self.mntdir,0711)

        #Creates a pipe to link the two subprocesses, and set the process
        parent_pipe, child_pipe = Pipe()
        self.pipe = parent_pipe
        self.process = Process(target=rootprocess.run,
                               args=(child_pipe,owner,self.filedir,self.mntdir))

        self.process.start()

        #The pipe needs to be locked on query, so that we don't have multiple at once
        self.q_lock = threading.Lock()

        #Dictionary of commands which are currently processing. The dict contains locks for
        #   each process
        self.processing = {}
        self.p_lock = threading.Lock()

        #If the "EOF" signal is sent, run this function
        self.eof = None

        #Start the commander thread
        self.cmdr = threading.Thread(target=self.recv)
        self.cmdr.daemon = True #The thread is daemonic, it shuts down with the program
        self.cmdr.start()

    
    def droproot(self):
        logger.info("Dropping to user %s"%(self.owner,))
        usertools.drop_privileges(self.owner)

    def recv(self):
        #The commander thread waits for results, and completes the queries associated with them
        while (True):
            cmd = self.pipe.recv()
            if (cmd=="EOF"):
                if (self.eof is not None):
                    self.eof(self)
            else:
                #The command should be valid (id,response) pair
                self.completeQuery(cmd[0],cmd[1])

    def addQuery(self):
        #Adds the query to the list of queries that are currently being processed

        #We acquire the lock, and only release it when the query is removed.
        #   This allows using l.acquire() to wait for completion
        l = threading.Lock()
        l.acquire()

        self.p_lock.acquire()
        r = random.randint(0,sys.maxint)
        while (r in self.processing):
            r = random.randint(0,sys.maxint)
        self.processing[r] = l
        self.p_lock.release()
        return (r,l)
    def completeQuery(self,qid,res):
        #Remove the query lock, and add the result to the dict.
        self.p_lock.acquire()
        if (qid in self.processing):
            self.processing[qid].release()
            self.processing[qid] = res
        self.p_lock.release()

    def remQuery(self,qid):
        #Returns the query result, and removes it from the dict
        res = None
        self.p_lock.acquire()
        if (qid in self.processing):
            res = self.processing[qid]
            del self.processing[qid]
        self.p_lock.release()
        return res

    def q(self,cmd):
        #Sends the given query

        r,l = self.addQuery()   #Adds the query to the list

        #Set the command's ID
        cmd["id"] = r

        self.q_lock.acquire()
        self.pipe.send(cmd)
        self.q_lock.release()

        return (r,l)

    def sync_q(self,cmd):
        #Synchronous version of query
        r,l = self.q(cmd)
        l.acquire() #Wait until the query is finished
        l.release()
        return self.remQuery(r)
    

    #File mainpulations
    def query(self,cmd):
        r = self.sync_q(cmd)
        if (r!="OK"):
            raise Exception(r)

    def makemount(self,container):
        #This is an internal function
        floc = os.path.join(os.path.relpath(self.mntdir),container)
        if not (os.path.isdir(floc)):
            if (os.path.exists(floc)):
                raise Exception(floc+" is not a directory!")
            else:
                os.mkdir(floc)
    def delmount(self,container):
        #This is an internal function.
        floc = os.path.join(os.path.relpath(self.mntdir),container)
        if (os.path.isdir(floc)):    #Deletes the decryption directory
            os.rmdir(floc)

    def create(self,container,password,size=64):
        if (self.exists(container)):
            raise Exception("Data file already exists!")

        self.makemount(container)
        try:
            self.query({"cmd": "create","size":size,"container":container,"pass":password})
        except:
            self.delmount(container)
            raise

    def open(self,container,password):
        if self.isopen(container):
            raise Exception("Container already open!")
        self.makemount(container)
        try:
            self.query({"cmd": "open","container":container,"pass":password})
        except:
            self.delmount(container)
            raise

    def close(self,container):
        self.query({"cmd": "close","container":container})
        self.delmount(container)
    def panic(self,container):
        self.query({"cmd": "panic","container":container})
        self.delmount(container)

    def panicall(self):
        self.query({"cmd": "panic","container":"*"})


    def shutdown(self):
        self.q_lock.acquire()
        self.pipe.send("EOF")
        self.q_lock.release()

    def join(self):
        self.shutdown() #Sending shutdown signal can be done many times - it won't cause harm
        self.process.join()
    

    def exists(self,container):
        #The path needs to be relativized to make sure we don't run into permissions issues
        return os.path.exists(os.path.join(os.path.relpath(self.filedir),container))
    
    def isopen(self,container):
        decloc = self.path(container)
        
        if (os.path.exists(decloc)):
            if (os.path.ismount(decloc)):
                return True
            #If the file exists, but is not mounted, then it was probably panic'd earlier
        return False

    def delete(self,container):
        self.panic(container)
        logger.warning("DELETE %s"%(container,))
        os.remove(os.path.join(os.path.relpath(self.filedir),container))

    def path(self,container):
        return  os.path.join(os.path.relpath(self.mntdir),container)



if (__name__=="__main__"):
    logging.basicConfig()
    import shutil

    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")

    f = FileCrypto("daniel","./test_db","./test_mnt")

    f.droproot()

    assert not f.exists("hello")
    assert not f.isopen("hello")

    f.create("hello","pass")

    assert f.exists("hello")
    assert f.isopen("hello")

    assert f.path("hello")=="test_mnt/hello"

    f.close("hello")

    assert f.exists("hello")
    assert not f.isopen("hello")

    f.open("hello","pass")

    assert f.exists("hello")
    assert f.isopen("hello")

    f.delete("hello")

    assert not f.exists("hello")
    assert not f.isopen("hello")

    f.join()

    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")