import os
from multiprocessing import Process, Pipe

from subprocess32 import call

import config
import usertools

from rootprocess import rootprocess
from userprocess import userprocess

#Get the configuration of the server
conf, logger = config.get()

#Check to make sure we are root

if (os.getuid() != 0):
    logger.critical("Run me as root!")
    exit(0)

#Create the data directory if it does not exist
if not os.path.exists(conf["datadir"]):
    os.mkdir(conf["datadir"])

if (conf["user"]==""):
    logger.critical("No user is set for server!")
    exit(0)

if not (usertools.userexists(conf["user"])):
    logger.warn("User %s does not exist, creating."%(conf["user"],))
    usertools.mkusr(conf["user"])

#Make sure that the data directory belongs to the user, and that nobody else can even read it
call(["chown","-R",conf["user"]+":"+conf["user"],conf["datadir"]])
call(["chmod","-R","770",conf["datadir"]])

def child(child_pipe,logger,cfg):
    #The child process will drop all privileges, and start a tornado server. The child process is where most
    #   of the interesting stuff happens.
    usertools.drop_privileges(cfg["user"])

    #Run the server
    userprocess.run(child_pipe,logger,cfg)

parent_pipe, child_pipe = Pipe()

p = Process(target=child,args=(child_pipe,logger,conf,))
p.start()

#Run the root process
rootprocess.run(parent_pipe,logger,conf)

p.join()
