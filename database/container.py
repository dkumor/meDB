
import os
from cryptoServer import client

class DatabaseContainer(object):
    """
    Given a container id, connects to it if it is open, or waits for a password if it is closed, and opens and prepares it
    once it is started up
    """
    
    fileLocation = "./db/"
    tmpLocation = "./tmp/"
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
        #We assume that an open container is non-empty - it is immediately populated with some files upon creation
        if (os.path.exists(self.decloc):
            if os.listdir(self.decloc):
                return True
        return False
            
    def create(self,password,size=10000):
        if (self.exists()):
            raise Exception("Data file already exists!")
        self.crypto.create(password,size)
        #Note: This 
        
    def open(self,password):
        if self.isopen():
            raise Exception("Container already open!")
        self.crypto.open(password)
        
    def close(self)
        self.crypto.close()
        os.rmdir(self.decloc)   #Deletes the decryption directory
        
    def forceClose(self):
        self.crypto.panic()
