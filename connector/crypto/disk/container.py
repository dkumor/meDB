
import os

class DatabaseContainer(object):
    """
    Given a container id, connects to it if it is open, or waits for a password if it is closed, and opens and prepares it
    once it is started up
    """

    crypto=None

    def __init__(self,dbid):
        if (self.crypto is None):
            raise Exception("FileCrypto not set")
        
        self.dbid = dbid

        
    def exists(self):
        return self.crypto.exists(self.dbid)

    def isopen(self):
        return self.crypto.isopen(self.dbid)

    def create(self,password,size=10000):
        self.crypto.create(self.dbid,password,size)

    def open(self,password):
        if self.isopen():
            raise Exception("Container already open!")

        self.crypto.open(self.dbid,password)
        

    def close(self):
        self.crypto.close(self.dbid)
        

    def panic(self):
        self.crypto.panic(self.dbid)
        

    def delete(self):
        self.crypto.delete(self.dbid)

    def name(self):
        return self.dbid

if (__name__=="__main__"):
    from filecrypto import FileCrypto
    import shutil

    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")

    f = FileCrypto("daniel","./test_db","./test_mnt")

    f.droproot()

    pwd = "testpassword"

    DatabaseContainer.crypto = f

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

    if (os.path.exists("./test_db")):
        shutil.rmtree("./test_db")
    if (os.path.exists("./test_mnt")):
        shutil.rmtree("./test_mnt")

    assert not x.exists()

    f.join()

    print "Done"
