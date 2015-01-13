import logging
logger = logging.getLogger("Setup")

from ..crypto.disk.filecrypto import FileCrypto
from ..crypto.disk import usertools
from subprocess32 import call
import os
import shutil
import getpass

class FileSetup(object):
    def __init__(self,dbdir,user,name,password = None,create=None,bindir=None,binoverwrite=False):

        if (os.getuid() != 0):
            raise Exception("Must be root to run FileSetup")

        #Now, start the FileCrypto process, which promises to decrypt the directory where files are held
        self.dbdir = os.path.abspath(dbdir)

        if not os.path.exists(self.dbdir):
            logger.info("Creating new database at '%s'",self.dbdir)
            os.makedirs(self.dbdir)
            #The DB directory is now OFF LIMITS
            #Java is a little bitch when it comes to relative paths - must have entire path readable.
            #so I can't make it so that the whole directory is off limits to everyone but root
            #call(["chmod","-R","000",self.dbdir])

        if (password is None):
            logger.info("Prompting for database password")
            password = getpass.getpass("Password for '"+str(name)+"':")

        #Create the filecrypto process
        rootmntdir = os.path.join(self.dbdir,"mnt")
        dbfiledir = os.path.join(self.dbdir,"db")
        self.fc = FileCrypto(user,dbfiledir,rootmntdir,mkusr=True)

        #Check if the container exists
        if not (self.fc.exists(name)):
            logger.warning("DBfile '%s' does not exist",name)

            if create is None or create < 64:
                logger.error("valid create value not given. Will not create dbfile.")
                self.close()
                raise Exception("Can't create container - 'create' not set correctly.")
            else:
                #Create a new container with the given name and password
                logger.warning("creating dbfile '%s'",name)
                try:
                    self.fc.create(name,password,size=create)
                except:
                    logging.error("couldn't create dbfile '%s'",name)
                    self.close()
                    raise

        else:
            logger.info("opening dbfile '%s'",name)
            try:
                self.fc.open(name,password)
            except:
                logging.error("couldn't open dbfile '%s'",name)
                self.close()
                raise

        #The dbfile is now open. Find the folder it is in
        self.mntdir = os.path.abspath(self.fc.path(name))

        logger.info('dbfile "%s" opened successfully',name)

        #Set up the bindir - make sure the right user owns it and symlink it to the dbfile
        bdir = os.path.join(self.mntdir,"bin")
        if (bindir is not None):
            bdir = os.path.join(self.mntdir,"bin")
            if ((not os.path.exists(bdir)) or binoverwrite):
                logger.info("setting up bindir using '%s'",bindir)
                if not (os.path.isdir(bindir)):
                    logger.error("bindir '%s' does not exist!",bindir)
                    self.close()
                    raise Exception("Given bindir does not exist.")
                if (os.path.exists(bdir)):
                    logger.warning("bindir exists in container - overwriting")
                    shutil.rmtree(bdir)

                #Copy the tree
                shutil.copytree(bindir,bdir)

                #Make sure that the user owns this bindir, and that permissions are restricted
                call(["chown","-R",user+":"+user,bdir])
                call(["chmod","-R","700",bdir])
            else:
                logger.info("bindir exists already")

        #Change the working directory to the dbdir
        os.chdir(self.mntdir)

        #Drop down to normal user
        logger.info("Dropping to user %s",user)
        usertools.drop_privileges(user)

    def close(self):
        self.fc.shutdown()
        self.fc.join()

if (__name__=="__main__"):
    from configuration import Configuration
    cfg = Configuration()
    f = FileSetup("./db","connector","default",create=64,bindir="./bin",binoverwrite=True)
    raw_input()
    f.close()