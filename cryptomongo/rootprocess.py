
import threading
import time

import multiluks


def runcommand(cmd,pipe,pipelock,luks):
    out = "OK"  #The output of a successful command is "OK"

    try:
        if (cmd["cmd"] == "create"):
            logger.info("LUKSCreate %(container)s (%(size)sM)",cmd)
            luks.create(cmd["container"],cmd["pass"],cmd["size"])

        elif (cmd["cmd"] == "open"):
            logger.info("LUKSOpen %(container)s",cmd)
            luks.open(cmd["container"],cmd["pass"])

        elif (cmd["cmd"] == "close"):
            logger.info("LUKSClose %(container)s",cmd)
            luks.close(cmd["container"])

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
        out = str(e)


    #Send theid of the finished process
    pipelock.acquire()
    pipe.send((cmd["id"],out))
    pipelock.release()

def run(pipe,logger,config):

    #First things first, set up luks
    luks = multiluks.MultiLuks(config["user"],
            os.path.join(config["datadir"],"db"),
            os.path.join(config["datadir"],"mnt"))

    #The pipe is going to be accessed from multiple threads, so we need
    #   to lock it
    pipelock = threading.Lock()

    #We keep an array of worker threads currently doing something
    threads = []

    while (True):

        #Read command
        r = pipe.recv()

        #Shut down if we get the shutdown signal
        if (r=="EOF"):
            break
        else:
            #Each command is run in an independent python thread, so that many commands
            #   can be executed at the same time
            t = threading.Thread(target=runcommand,args = (r,pipe,pipelock,luks))
            t.daemon =False
            t.start()
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
    logger = logging.getLogger("test")

    run(parent_pipe,logger,config)

    p = Process(target=run,args=(child_pipe,logger,conf,))
    p.start()
