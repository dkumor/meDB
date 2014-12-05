import argparse
import ConfigParser
import os
import logging

class Configuration(object):
    """
    This class holds the configuration of the program. It loads every parameter both from files
    and from the command line
    """

    cfg = None
    logformat = "%(levelname)s:%(name)s:%(created)f - %(message)s"

    argtypes = {
        "server": {
            "port": {"s": "p","help": "port number to launch server on","type": int},
            "dbdir": {"s":"d","help": "directory where dbfiles are located","default":"./db"},
            "mntdir": {"s":"m","help": "directory where dbfiles will be mounted","default":"./mnt"},
            "user": {"s": "u","help": "user from which to run"},
            "password": {"help": "Password to decrypt dbfile"},
            "dbfile": {"help": "The dbfile to open"},
            "connector":{"help": "Address of connector server"}
        }
        }

    def __init__(self,rootname=None,description="",args = "server"):

        #Run setup only if the config is not None
        if (Configuration.cfg is None):
            self.initLogger()

            #Check if args is a preset
            if (args in Configuration.argtypes):
                args = Configuration.argtypes[args]
            cmdline = self.initArgs(description,args)

            #Load a config file if given
            if (cmdline.config is not None):
                Configuration.cfg = self.loadFile(cmdline.config)
            else:
                Configuration.cfg = {}

            #The logfile is a default argument, so set it here
            if (cmdline.config is not None):
                Configuration.cfg["logfile"] = cmdline.config

            #This automatically loads into cfg variable
            self.loadCommandline(cmdline,args)

    def initLogger(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.propagate= False

        #Write log messages to console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(Configuration.logformat))
        logger.addHandler(ch)
        
    def logfile(self,fname):
        #Add a log file to which to log
        ch = logging.handlers.RotatingFileHandler(fname,maxBytes = 1024*1024*10,backupCount=5)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(Configuration.logformat))
        
        logging.getLogger().addHandler(ch)
        

    def initArgs(self,description,args):
        parser = argparse.ArgumentParser(description=description)

        #The configuration file to load.
        parser.add_argument("-c","--config",help="The configuration file to use")

        #The following options override values within the configuration file
        parser.add_argument("-l","--logfile",help="The log file location")

        for arg in args:
            a  = {"help": args[arg]["help"]}
            if ("type" in args[arg]):
                a["type"] = args[arg]["type"]
            if ("default" in args[arg]):
                a["default"] = args[arg]["default"]
            if ("nargs" in args[arg]):
                a["nargs"] = args[arg]["nargs"]
            sec = None
            if ("s" in args[arg]):
                sec = "-"+args[arg]["s"]

            if (arg[0]==">"):
                arg = arg[1:]
            else:
                arg= "--"+arg

            if (sec is not None):
                parser.add_argument(sec,arg,**a)
            else:
                parser.add_argument(arg,**a)

        return parser.parse_args()


    def loadFile(self,fname,dbname=None):
        pass

    def loadCommandline(self,cmd,args):
        pass


if (__name__=="__main__"):
    l = logging.getLogger("hello")

    l.error("Here is 1")

    Configuration()

    l.error("Here is 2")