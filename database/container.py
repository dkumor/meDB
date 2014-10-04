
import os
from meDB.cryptoServer import client

class DatabaseContainer(object):
    """
    Given a container id, connects to it if it is open, or waits for a password if it is closed, and opens and prepares it
    once it is started up
    """
    
    fileLocation = "./db/"
    tmpLocation = "./mnt/"
    def __init__(self,dbid):
        self.dbid = dbid
        
        floc = os.path.abspath(self.fileLocation)
        tloc = os.path.abspath(self.tmpLocation)
        
        #Create file location folder if it doesnt exist
        if not (os.path.isdir(floc)):
            if (os.path.exists(floc)):
                raise Exception(floc+" is not a directory!")
            else:
                os.makedirs(floc)
                
        if not (os.path.isdir(tloc)):
            if (os.path.exists(tloc)):
                raise Exception(tloc+" is not a directory!")
            else:
                os.makedirs(tloc)
        
        #Create data file and decryption locations
        self.datafile = os.path.join(floc,dbid)
        self.decloc = os.path.join(tloc,dbid)
        
        #Create crypto object for reading encrypted database
        self.crypto = client.Crypto(self.datafile,self.decloc)
        
    def exists(self):
        return os.path.exists(self.datafile)
        
    def isopen(self):
        #We assume that a closed container deletes its mount directory
        if (os.path.exists(self.decloc)):
            return True
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
        
        #Note: This 
        
    def open(self,password):
        if self.isopen():
            raise Exception("Container already open!")
        os.mkdir(self.decloc)
        try:
            self.crypto.open(password)
        except:
            os.rmdir(self.decloc)
            raise
        
    def close(self):
        self.crypto.close()
        os.rmdir(self.decloc)   #Deletes the decryption directory
        
    def forceClose(self):
        self.crypto.panic()
        os.rmdir(self.decloc)
        
if (__name__=="__main__"):
    DatabaseContainer.fileLocation = "./test_db"
    DatabaseContainer.tmpLocation = "./test_tmp"
    
    import shutil
    pwd = "testpassword"
    
    if (os.path.exists(DatabaseContainer.fileLocation)):
        shutil.rmtree(DatabaseContainer.fileLocation)
    if (os.path.exists(DatabaseContainer.tmpLocation)):
        shutil.rmtree(DatabaseContainer.tmpLocation)
    
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
    shutil.rmtree(DatabaseContainer.tmpLocation)
    
    assert not x.exists()
