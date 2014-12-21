"""
Initialize the basics.
"""

import logging
import os
from subprocess32 import call
from configuration import Configuration
from ..crypto.disk.filecrypto import FileCrypto
from ..crypto.disk import usertools

import getpass

logger = logging.getLogger("Setup")

class ServerSetup(object):
    def __init__(self,description=""):

        if (os.getuid() != 0):
            raise Exception("Must be root to start server")

        cfg = Configuration({
            "port": {"s": "p","help": "port number to launch server on","type": int},
            "dbdir": {"s":"d","help": "directory where dbfiles are located","default":"./db"},
            "user": {"s": "u","help": "user from which to run","default":"connector"},
            "password": {"help": "Password to decrypt dbfile"},
            "connector":{"help": "Address of connector server"},
            "create":{"help": "If this is set, create the dbfile with the given size if does not exist","type": int}
        },description)

        if not (usertools.userexists(cfg["user"])):
            logger.warn("User %s does not exist, creating.",cfg["user"])
            usertools.mkusr(cfg["user"])

        #Now, start the FileCrypto process, which promises to decrypt the directory where files are held
        self.dbdir = os.path.abspath(cfg["dbdir"])

        if not os.path.exists(self.dbdir):
            logger.info("Creating new database at '%s'",self.dbdir)
            os.makedirs(self.dbdir)

        #Change the working directory to the dbdir
        os.chdir(self.dbdir)

        #Now, create the mount and dbfile directories
        rootmntdir = os.path.join(self.dbdir,"mnt")
        dbfiledir = os.path.join(self.dbdir,"db")
        if not os.path.exists(rootmntdir):
            logger.info("Setting up mountpoints")
            os.mkdir(rootmntdir)
        if not os.path.exists(dbfiledir):
            logger.info("Setting up database folder")
            os.mkdir(dbfiledir)

        #Make sure that the db directory belongs to the user, and that nobody else can even read it
        call(["chown","-R",cfg["user"]+":"+cfg["user"],self.dbdir])
        call(["chmod","-R","770",cfg["dbdir"]])

        password = cfg["password"]
        if (password is None):
            logger.info("Prompting for password")
            password = getpass.getpass("Password for '"+str(cfg["name"])+"':")

        #Create the filecrypto process
        self.fc = FileCrypto(cfg["user"],dbfiledir,rootmntdir)

        #Drop down to normal user
        logger.info("Dropping to user %s",cfg["user"])
        usertools.drop_privileges(cfg["user"])

        #Check if the container exists
        if not (self.fc.exists(cfg["name"])):
            logger.warning("Dbfile '%s' does not exist",cfg["name"])

            if cfg["create"] is None or cfg["create"] < 64:
                logger.error("valid create value not given. Will not create dbfile.")
                self.close()
                raise Exception("Can't create container - 'create' not set correctly.")
            else:
                #Create a new container with the given name and password
                logger.warning("creating dbfile '%s'",cfg["name"])
                try:
                    self.fc.create(cfg["name"],password,size=cfg["create"])
                except:
                    logging.error("couldn't create dbfile '%s'",cfg["name"])
                    self.close()
                    raise

        else:
            logger.info("opening dbfile '%s'",cfg["name"])
            try:
                self.fc.open(cfg["name"],password)
            except:
                logging.error("couldn't open dbfile '%s'",cfg["name"])
                self.close()
                raise

        #The dbfile is now open. Find the folder it is in
        self.mntdir = self.fc.path(cfg["name"])

        logger.info('dbfile opened successfully')

    def close(self):
        self.fc.shutdown()


if (__name__=="__main__"):
    ServerSetup().close()