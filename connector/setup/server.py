"""
Initialize the basics.
"""

import logging
import os
import socket

from configuration import Configuration
from file import FileSetup

logger = logging.getLogger("Setup")


#Gets a random port to open
def get_open_port():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        port = s.getsockname()[1]
        s.close()
        return port

class ServerSetup(object):
    def __init__(self,description="",port=0,
                 bindir=None,binoverwrite=False,zoorequire=False):
        
        #Set the default port
        self.port = port
        self.fs = None

        cfg = Configuration({
            "port": {"s": "p","help": "port number to launch server on","type": int},
            "dbdir": {"s":"d","help": "directory where dbfiles are located","default":"./db"},
            "user": {"s": "u","help": "user from which to run","default":"connector"},
            "password": {"help": "Password to decrypt dbfile"},
            "zookeeper":{"help": "Address of zookeeper server (used for distributed server)"},
            "create":{"help": "If this is set, create the dbfile with the given size if does not exist","type": int},
            "hostname": {"help": "The hostname (or ip) to use for registering the server","default":socket.gethostname()}
        },description)

        #If running servers in standalone mode, the address of the zookeeper server is required.
        if (cfg["zookeeper"] is not None):
            self.zookeeper = cfg["zookeeper"]
        elif (zoorequire):
            raise Exception("Address of zookeeper server not set in config!")

        self.fs = FileSetup(cfg["dbdir"],cfg["user"],cfg["name"],password=cfg["password"],create=cfg["create"],
                            bindir=bindir,binoverwrite=binoverwrite)

        #Now set the port if it is valid
        if (cfg["port"] is not None):
            self.port = cfg["port"]

        #Create a random port if port is not set
        if self.port <= 0:
            self.port = int(get_open_port())

        self.hostname = str(cfg["hostname"])

        logger.info("Using port %i for server",self.port)

    def close(self):
        if (self.fs is not None):
            self.fs.close()
        self.fs = None

    def __del__(self):
        self.close()


if (__name__=="__main__"):
    s= ServerSetup()
    print s.fs.mntdir
    print s.port
    s.close()