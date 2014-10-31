"""
RootCommander: Handles all communication with the rootprocess, and makes sure everything is nice and
threadsafe. There can only be ONE rootcommander object. It commands the root - don't want these fuckers
to interfere with each other
"""

import threading
import random
import sys

class RootCommander(object):
    def __init__(self,pipe):
        self.pipe = pipe

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


    def recv(self):
        #The commander thread waits for results, and completes the queries associated with them
        while (True):
            cmd = self.pipe.recv()
            if (cmd=="EOF"):
                break
            else:
                #The command should be valid (id,response) pair
                self.completeQuery(cmd[0],cmd[1])

        if (self.eof is not None):
            self.eof()


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

if (__name__=="__main__"):
    from rootprocess import run
    from multiprocessing import Process, Pipe
    import logging
    import os

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

    logger = logging.getLogger("rootprocess")
    logging.basicConfig()
    logger.setLevel(logging.INFO)

    p, child_pipe = Pipe()



    child = Process(target=run,args=(child_pipe,logger,conf,))
    child.start()


    rc = RootCommander(p)

    print rc.sync_q({"cmd": "create",
        "container": "lol",
        "pass": "pwd",
        "size": 64
    })
    print rc.sync_q({"cmd": "close",
        "id": 2,
        "container": "lol",
    })


    p.send("EOF")
    child.join()

    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")

    print "DONE"
