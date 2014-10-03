import os

import mongod
from container import DatabaseContainer

class MongoContainer(DatabaseContainer):
    """
    Opens a container and starts a mongoDB database within
    """
    smallSize = 4000
    def __init__(self,dbid):
        DatabaseContainer.__init__(self,dbid)
        self.isopener = False
        
        
        self.connection = None
        self.cur = None
        
        self.dbfolder = os.path.join(self.decloc,"db")
        self.portfile = os.path.join(self.decloc,"port")
        
    def create(self,password,size=10000):
        DatabaseContainer.create(self,password,size)
        self.isopener = True
        
        #The container is now mounted, so we create the database folder (db)
        os.mkdir(self.dbfolder)
        
        smallFiles = (size <= self.smallSize)
        
        self.connection = mongod.Connection(self.dbfolder,smallFiles)
        self.cur = self.connection.cursor()
        
        #Write the port number to a file
        with open(self.portfile,"w") as f:
            f.write(str(self.connection.port))
        
        
    def open(self,password):
        if (self.isopen()):
            portnm = 0
            #Read the port number from the file
            with open(self.portfile,"r") as f:
                portnum = int(f.read())
            if (portnum < 27017):
                raise Exception("Read portnum that is in weird range")
                
            self.cur = mongod.getCursor(portnum)
        else:
            DatabaseContainer.open(self,password)
            self.isopener = True
            
            #Check if we should start the database in small-file mode
            smallFiles = (int(os.path.getsize(self.datafile)*1e-6) <=self.smallSize)
            print "smallFile:",smallFiles
            
            self.connection = mongod.Connection(self.dbfolder,smallFiles)
            
            self.cur = self.connection.cursor()
        
            #Write the port number to a file
            with open(self.portfile,"w") as f:
                f.write(str(self.connection.port))
            
    def cursor(self):
        return self.cur
        
        
    def close(self):
        if (self.connection!=None):
            self.connection.close()
        if (self.isopener):
            DatabaseContainer.close()
