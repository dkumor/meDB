import argparse
import ConfigParser
import os
import logging

def argParse():
    #Reads command line arguments

    parser = argparse.ArgumentParser(description="Runs cryptomongo database service.")
    #The configuration file to load.
    parser.add_argument("-c","--config",help="The configuration file to use")
    #The following options override values within the configuration file
    parser.add_argument("-l","--logfile",help="The log file location")
    parser.add_argument("-p","--port",help="The port number to launch server on",type=int)
    parser.add_argument("-d","--datadir",help="The root directory from which to run cryptoMongo")
    parser.add_argument("-u","--user",help="Set the username from which to run")
    parser.add_argument("--key",help="File for root CA private key")
    parser.add_argument("--cert",help="File for root CA certificate")
    return parser.parse_args()

def configParse(cfg):
    if not (os.path.exists(cfg["cfile"])):
        raise Exception("Could not find configuration file")

    #Reads configuration file
    config = ConfigParser.SafeConfigParser()
    config.read(cfg["cfile"])


    try: cfg["port"] = int(config.get("cryptomongo","port"))
    except: pass
    try: cfg["logfile"]= config.get("cryptomongo","logfile")
    except: pass
    try: cfg["datadir"]= config.get("cryptomongo","datadir")
    except: pass
    try: cfg["key"]= config.get("cryptomongo","key")
    except: pass
    try: cfg["cert"]= config.get("cryptomongo","cert")
    except: pass
    try: cfg["user"]= config.get("cryptomongo","user")
    except: pass

    return cfg

def conf():
    cfg = {
        "logfile": "",
        "port": 49200,
        "cfile": "",
        "datadir": "./cryptomongo",
        "user": "cryptomongo",
        "key": '',
        "cert": '',
        "address":"127.0.0.1"
    }

    a = argParse()

    #The argument can override arguments that can change stuff in the config file
    if (a.config is not None):
        cfg["cfile"] = os.path.abspath(a.config)

    #Parse the config file
    if (cfg["cfile"]!=""):
        cfg = configParse(cfg)

    #Overwrite config with any command line arguments
    if (a.datadir):
        cfg["datadir"] = a.datadir

    cfg["datadir"] = os.path.abspath(cfg["datadir"])


    if (a.port):
        cfg["port"] = a.port
    if (a.logfile):
        cfg["logfile"] = os.path.abspath(a.logfile)
    if (a.cert):
        cfg["cert"] = a.cert
    if (a.key):
        cfg["key"] = a.key
    if (a.user):
        cfg["user"] = a.user


    #Now set several things that are not in the configuration
    cfg["mntdir"] = os.path.join(cfg["datadir"],"mnt")
    cfg["dbdir"] = os.path.join(cfg["datadir"],"db")
    cfg["port"] = int(cfg["port"])
    return cfg

def getLogger(cfg):
    logger = logging.getLogger("cryptomongo")
    logger.setLevel(logging.INFO)
    FORMAT = "%(asctime)s %(levelname)s - %(message)s"

    ch = logging.StreamHandler()
    #ch.setLevel(logging.WARNING)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(ch)
    if (cfg["logfile"]):
        ch2 = logging.handlers.RotatingFileHandler(cfg["logfile"],maxBytes = 1024*1024*10,backupCount=5)
        ch2.setLevel(logging.INFO)
        ch2.setFormatter(logging.Formatter(FORMAT))
        logger.addHandler(ch2)
    logger.propagate = False
    return logger


def get():
    #Reads all command line arguments, configuration files, and generates the logger
    cfg = conf()
    logger = getLogger(cfg)
    logger.info("Loaded configuration: " + str(cfg))
    return cfg, logger
