
import threading


from database import cryptomongo

class MongoStore(object):
    """
    Stores all mongoDB databases and makes sure that they are all contained correctly
    """
    logger = None
    
    def __init__(self):
        if (self.logger is None):
            raise Exception("Logger is not set")

        self.databases = {}
        self.d_lock = threading.Lock()


    def open(self,dbid):
        pass

    def close(self,dbid):
        pass

    def create(self,dbid):
        pass

    def delete(self,dbid):
        pass

    def panic(self,dbid):
        pass

    def panicall(self):
        pass
