
import threading
import time

import luks

containers = {}
ctrmtx = threading.Lock()
def runcommand(cmd,pipe,m,usr):
    global containers
    global ctrmtx

    out = "OK"
    setnone = False
    try:
        if (cmd["cmd"] == "create"):
            logger.info("LUKSCreate %(container)s (%(size)sM)-> %(mountpoint)s",cmd)

            ctrmtx.acquire()
            if (cmd["container"] in containers):
                ctrmtx.release()
                raise Exception("Container already created")
            containers[cmd['container']] = None #Set to None to signify that we are creating it
            setnone = True
            ctrmtx.release()

            lcntnr= luks.CryptoLuks(cmd["container"],cmd["mountpoint"])
            lcntnr.create(cmd["pass"],owner=usr,fsize=cmd["size"])
            containers[cmd['container']] = lcntnr
        elif (cmd["cmd"] == "open"):
            logger.info("LUKSOpen %(container)s -> %(mountpoint)s",cmd)
            opn = False

            while (cmd["container"] in containers and containers[cmd['container']] is None):
                logger.info("LUKSOpen waiting for %(container)s",cmd)
                time.sleep(0.5)
            ctrmtx.acquire()
            if (cmd["container"] in containers):
                ctrmtx.release()
                logger.info("LUKSOpen (already open) %(container)s",cmd)
            else:
                containers[cmd['container']] = None #Set to None to signify that we are already opening it
                setnone = True
                ctrmtx.release()

                lcntnr = luks.CryptoLuks(cmd["container"],cmd["mountpoint"])
                lcntnr.open(cmd["pass"])
                containers[cmd['container']] = lcntnr
        elif (cmd["cmd"] == "close"):
            logger.info("LUKSClose %(container)s",cmd)
            while (cmd["container"] in containers and containers[cmd['container']] is None):
                logger.info("LUKSClose waiting for %(container)s",cmd)
                time.sleep(0.5)
            ctrmtx.acquire()
            if (cmd["container"] in containers):
                containers[cmd["container"]].close()
                del containers[cmd["container"]]
            ctrmtx.release()
        elif (cmd["cmd"] == "panic"):

            if (cmd["container"]=="*"):
                logger.critical("CRYPTO TOTAL PANIC - HOLY FUCKING SHIT, WE'RE FUCKED")
                ctrmtx.acquire()
                while (len(containers)>0):
                    for k in containers:
                        if (containers[k] != None):
                            containers[k].panic()
                            del containers[k]
                    if (len(containers)>0):
                        logger.warning("TOTAL PANIC waiting for containers...")
                        time.sleep(0.5)

                logger.warning("All containers closed.")

            else:
                while (cmd["container"] in containers and containers[cmd['container']] is None):
                    logger.warning("PANIC waiting for %(container)s",cmd)
                    time.sleep(0.5)
                ctrmtx.acquire()
                if (cmd['container'] in containers):
                    logger.warning(" %(container)s - PANIC",d)

                    containers[cmd["container"]].panic()
                    del containers[cmd["container"]]
                    logger.warning(" %(container)s - closed",d)
            ctrmtx.release()


    except Exception, e:
        out = str(e)
        #If there was an error, delete the placeholder
        if (setnone==True and containers[cmd['container']]==None):
            del containers[cmd['container']]

    #Send theid of the finished process
    m.acquire()
    pipe.send((cmd["id"],out))
    m.release()

def run(pipe,logger,config):
    global containers

    logger.info("Running root process")
    m = threading.Lock()

    thr = []

    while (True):
        r = pipe.recv()
        logger.info("RECV: %s"%(str(r),))

        #Make sure it isn't the shutdown signal
        if (r=="EOF"):
            break
        else:
            #Each command is run in an independent python thread, so that many commands
            #   can be executed at the same time
            t = threading.Thread(target=runcommand,args = (r,pipe,m,config["user"],))
            t.daemon =False
            t.start()
            thr.append(t)

            #Remove finished threads
            for t in my_threads:
                if not t.isAlive():
                    # get results from thtead
                    t.handled = True
            thr = [t for t in thr if not t.handled]

    #Wait until all threads join
    logger.info("Waiting for threads to join")
    for i in thr:
        i.join()
    logger.info("Shutting down all containers")
    for k in containers:
        containers[k].panic()
    containers.clear()


    logger.info("Root process finished")

if (__name__=="__main__"):
    from multiprocessing import Process, Pipe
    import logging
    logger = logging.getLogger("test")

    run(parent_pipe,logger,config)

    p = Process(target=run,args=(child_pipe,logger,conf,))
    p.start()
