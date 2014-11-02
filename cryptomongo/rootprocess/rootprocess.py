import signal
import threading
import time
import os

from luks.multiluks import MultiLuks


def runcommand(cmd,logger,pipe,pipelock,luks):
    out = "OK"  #The output of a successful command is "OK"

    try:
        if (cmd["cmd"] == "create"):
            logger.info("LUKSCreate %(container)s (%(size)sM)",cmd)
            luks.create(cmd["container"],cmd["pass"],cmd["size"])
            logger.info("LUKSCreate %(container)s OK",cmd)
        elif (cmd["cmd"] == "open"):
            logger.info("LUKSOpen %(container)s",cmd)
            luks.open(cmd["container"],cmd["pass"])
            logger.info("LUKSOpen %(container)s OK",cmd)
        elif (cmd["cmd"] == "close"):
            logger.info("LUKSClose %(container)s",cmd)
            luks.close(cmd["container"])
            logger.info("LUKSClose %(container)s OK",cmd)
        elif (cmd["cmd"] == "panic"):

            if (cmd["container"]=="*"):
                logger.critical("CRYPTO TOTAL PANIC - HOLY FUCKING SHIT, WE'RE FUCKED")
                luks.panicall()
                logger.warning("PANIC: All containers closed.")

            else:
                logger.warning("PANIC - %(container)s",cmd)
                luks.panic(cmd["container"])
                logger.warning("PANIC %(container)s closed",cmd)

    except Exception, e:
        logger.warning("Root RunCommand exception: %s"%(str(e),))
        out = str(e)


    #Send theid of the finished process
    pipelock.acquire()
    pipe.send((cmd["id"],out))
    pipelock.release()

def run(pipe,logger,config):
    logger.info("Running root process")

    #First things first, set up luks
    luks = MultiLuks(config["user"],config["dbdir"],config["mntdir"])

    #The pipe is going to be accessed from multiple threads, so we need
    #   to lock it
    pipelock = threading.Lock()

    #Send the child an EOF if we get a signal
    def handleSignal(*args):
        pass
        """
        pipelock.acquire()
        pipe.send("EOF")
        pipelock.release()
        """

    signal.signal(signal.SIGINT,handleSignal)

    #We keep an array of worker threads currently doing something
    threads = []

    while (True):

        #Read command
        r = pipe.recv()

        #Shut down if we get the shutdown signal
        if (r=="EOF"):
            logger.info("Recv EOF cmd")
            break
        else:
            #Each command is run in an independent python thread, so that many commands
            #   can be executed at the same time
            t = threading.Thread(target=runcommand,args = (r,logger,pipe,pipelock,luks))
            t.daemon =False
            t.start()
            t.handled = False
            threads.append(t)

            #Remove finished threads
            for t in threads:
                if not t.isAlive():
                    # get results from thtead
                    t.handled = True
            threads = [t for t in threads if not t.handled]

    #Wait until all threads join
    logger.info("Waiting for threads to join")
    for i in threads:
        i.join()
    logger.info("Shutting down all containers")
    luks.panicall()
    logger.info("Root command process finished")

if (__name__=="__main__"):
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

    logger = logging.getLogger("rootprocess")
    logging.basicConfig()
    logger.setLevel(logging.INFO)

    p, child_pipe = Pipe()



    child = Process(target=run,args=(child_pipe,logger,conf,))
    child.start()


    p.send({"cmd": "create",
        "id": 1,
        "container": "lol",
        "pass": "pwd",
        "size": 64
    })
    p.send({"cmd": "close",
        "id": 2,
        "container": "lol",
    })

    print p.recv()
    print p.recv()

    p.send("EOF")
    child.join()


    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")

    print "DONE"
