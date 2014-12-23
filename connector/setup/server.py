"""
Initialize the basics.
"""

import logging
import os

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
                 bindir=None,binoverwrite=False):
        
        #Set the default port
        self.port = port

        cfg = Configuration({
            "port": {"s": "p","help": "port number to launch server on","type": int},
            "dbdir": {"s":"d","help": "directory where dbfiles are located","default":"./db"},
            "user": {"s": "u","help": "user from which to run","default":"connector"},
            "password": {"help": "Password to decrypt dbfile"},
            "connector":{"help": "Address of connector server"},
            "create":{"help": "If this is set, create the dbfile with the given size if does not exist","type": int}
        },description)

        self.fs = FileSetup(cfg["dbdir"],cfg["user"],cfg["name"],password=cfg["password"],create=cfg["create"],
                            bindir=bindir,binoverwrite=binoverwrite)

        #Now set the port if it is valid
        if (cfg["port"] is not None):
            self.port = cfg["port"]

        #Create a random port if port is not set
        if self.port <= 0:
            self.port = int(get_open_port())

        logger.info("Using port %i for server",self.port)

    def close(self):
        self.fs.close()


if (__name__=="__main__"):
    s= ServerSetup()
    print s.fs.mntdir
    print s.port
    s.close()