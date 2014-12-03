
from datastore.datastore import DataStore

#We define a custom exception to handle the actions of the user
class PermissionDenied(Exception):
    pass

class User(object):
    """
    This class exposes the datastore as the specific user sees it. In particular, it maintains and
    enforces all restrictions and permissions for the specific user.
    """

    def __init__(self,ds,usr,secret=None):
        self.ds = ds

        #Try loading the user
        if (secret is not None):
            self.usr = self.ds.users(usr,secret)
        else:
            self.usr = self.ds.users.get(usr)

        #Make sure that the user was extracted
        if (self.usr is None):
            raise PermissionDenied()

    def reload(self):
        #Reload the user from the database
        self.usr = self.ds.users.get(self.usr.id)

    #The single most important function that the user has - write data to the database
    def write(self,data,timestamp=None):
        if not (self.usr.write):
            raise PermissionDenied()
        else:
            self.ds.inputs.add(self.usr.id,data,timestamp)

    #Read data from the database subject to permission clusterf*ck
    def read(self,users=None,attributes=None,starttime=None,endtime=None):
        if (not self.usr.pRead("db")):
            #We don't have unlimited reading access - so make sure we are allowed to read this shit
            if (users is None):
                #users is None, so we want results of all permitted users.
                users = list(self.usr.readset())
            else:
                if (isinstance(users,str)):
                    if not (str(users) in self.usr.readset()):
                        raise PermissionDenied()
                else:
                    users = list(set(users).intersection(self.usr.readset()))
                    if (len(users)==0):
                        raise PermissionDenied()

        return self.ds.inputs.get(users,attributes,starttime,endtime)


    #Registering and unregistering inputs
    def register(self,name,meta = {}):
        if not (self.usr.pWriteInputs(self.usr.id) or self.usr.pWriteInputs("db")):
            raise PermissionDenied()
        else:
            #We don't explicitly run addInput, since we want to keep
            #   any additional metadata that might already exist in the register
            self.usr.input(name,setv=meta)

    def unregister(self,name):
        if not (self.usr.pWriteInputs(self.usr.id) or self.usr.pWriteInputs("db")):
            raise PermissionDenied()
        else:
            self.usr.remInput(name)

    def getinput(self,name):
        if not (self.usr.pRead(self.usr.id) or self.usr.pRead("db")):
            raise PermissionDenied()
        else:
            return self.usr.getInput(name)

    def intersectOutputs(self,outputs):
        #Returns intersection of outputs and the outputs the user is allowed to trigger
        res = []
        for o in outputs:
            #If the output in question o is in the list of trigger outputs
            if (self.usr.output(o)): # or the output's parent is permitted
                res.append(o)

    def mkuser(self,perm={},write=False,create=False,outputs=[]):
        if not (self.usr.create):
            raise PermissionDenied()
        else:
            if not self.usr.write:
                write = False   #If this user can't write, then the child sure as hell can't



if (__name__=="__main__"):
    #Change the file locations of the container for testing
    MongoContainer.fileLocation = "./test_db"
    MongoContainer.tmpLocation = "./test_mnt"

    cname = "adfdsf"
    dname = "adfsfd"
    cpwd = "password"

    import shutil
    import time

    if (os.path.exists(MongoContainer.fileLocation)):
        shutil.rmtree(MongoContainer.fileLocation)
    if (os.path.exists(MongoContainer.tmpLocation)):
        shutil.rmtree(MongoContainer.tmpLocation)

    #Open a datastore
    ds = DataStore(cname,dname,cpwd,create = True)

    ds.users.create()


    ds.close()

    print "\n\nAll tests completed successfully!"
