
import os
import cryptfile

class DatabaseContainer(object):
    """
    Given a container id, connects to it if it is open, or waits for a password if it is closed, and opens and prepares it
    once it is started up
    """

    fileLocation = "./db/"
    mntLocation = "./mnt/"
    def __init__(self,dbid):
        self.dbid = dbid

        #We must do all file operations relative to the current directroy due to issues with
        #   permissions in parent directories.
        floc = os.path.relpath(self.fileLocation)
        tloc = os.path.relpath(self.mntLocation)

        #Create file location folder if it doesnt exist
        if not (os.path.isdir(floc)):
            if (os.path.exists(floc)):
                raise Exception(floc+" is not a directory!")
            else:
                os.mkdir(floc)

        if not (os.path.isdir(tloc)):
            if (os.path.exists(tloc)):
                raise Exception(tloc+" is not a directory!")
            else:
                os.mkdir(tloc)

        #Create data file and decryption locations
        self.datafile = os.path.join(floc,dbid)
        self.decloc = os.path.join(tloc,dbid)

        #Create crypto object for reading encrypted database
        self.crypto = cryptfile.FileCrypto(self.dbid)

    def exists(self):
        return os.path.exists(self.datafile)

    def isopen(self):
        #We assume that a closed container deletes its mount directory
        if (os.path.exists(self.decloc)):
            if (os.path.ismount(self.decloc)):
                return True
            #If the file exists, but is not mounted, then it was probably panic'd earlier
        return False

    def create(self,password,size=10000):
        if (self.exists()):
            raise Exception("Data file already exists!")
        os.mkdir(self.decloc)

        try:
            self.crypto.create(password,size)
        except:
            os.rmdir(self.decloc)
            raise

    def open(self,password):
        if self.isopen():
            raise Exception("Container already open!")

        #Panic does nto automatically delete the directories, so only create if necessary
        if not (os.path.exists(self.decloc)):
            os.mkdir(self.decloc)
        else:
            if (not os.path.isdir(self.decloc) or os.path.ismount(self.decloc)):
                raise Exception("It looks like the container is open... Did stuff crash earlier?")
        try:
            self.crypto.open(password)
        except:
            os.rmdir(self.decloc)
            raise

    def close(self):
        self.crypto.close()
        if (os.path.isdir(self.decloc)):    #Deletes the decryption directory
            os.rmdir(self.decloc)

    def panic(self):
        self.crypto.panic()
        if (os.path.isdir(self.decloc)):
            os.rmdir(self.decloc)

    def delete(self):
        self.panic()
        os.remove(self.datafile)

    def name(self):
        return self.dbid

if (__name__=="__main__"):

    import sys

    sys.path.append(os.path.abspath("../"))
    sys.path.append(os.path.abspath("../../"))
    from rootprocess.rootprocess import run
    from rootcommander import RootCommander
    from multiprocessing import Process, Pipe
    import logging
    import os

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

    logger = logging.getLogger("container")
    logging.basicConfig()
    logger.setLevel(logging.INFO)

    p, child_pipe = Pipe()



    child = Process(target=run,args=(child_pipe,logger,conf,))
    child.start()


    rc = RootCommander(p)
    cryptfile.FileCrypto.rootcommander = rc
    DatabaseContainer.fileLocation = "./test_db"
    DatabaseContainer.mntLocation = "./test_mnt"

    pwd = "testpassword"



    x = DatabaseContainer("testContainer")

    print "Checking preliminary"
    assert not x.isopen()
    assert not x.exists()

    print "Creating..."
    x.create(pwd,64)

    assert x.exists()
    assert x.isopen()
    print "Closing..."
    x.close()

    assert not x.isopen()
    assert x.exists()
    print "Opening"
    x.open(pwd)

    assert x.isopen()
    print "Closing"
    x.close()

    print "Cleaning up"


    shutil.rmtree(DatabaseContainer.fileLocation)
    shutil.rmtree(DatabaseContainer.mntLocation)

    assert not x.exists()

    p.send("EOF")
    child.join()

    print "Done"
