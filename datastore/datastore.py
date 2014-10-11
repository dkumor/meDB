from database.cryptomongo import MongoContainer

class DataStore(object):
    def __init__(self,dbid,password=None,size=None):
        #Given an ID of the datastore, connect to it. 
        #If given a password, open if possible. If given password and size, create if necessary.
        
        
        #Opens the container - and creates it if necessary
        self.container = MongoContainer(dbid)
        if not (self.container.exists()):
            if (password != None and size >= 1000):
                self.container.create(password,size)
            else:
                raise Exception("Container does not exist")
        else:
            self.container.open(password)
            
        self.db = self.container.cursor().datastore
        
