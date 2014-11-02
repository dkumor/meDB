"""
The Crypto object: it wraps the rootcommander object to allow for encrypting containers at rest.

As a side note: I really don't like the fact that rootcommander needs to be set in order for the function to work.
The rootcommander comes from the "top" of the execution tree, but it is only used at the very bottom, since it is a very
low level communication device. I am not sure what I want to do about that. For now, I guess that the rootcommander simply needs to be set
by the higher level functions - as a sort of global variable for the entire program.
"""

class FileCrypto(object):
    rootcommander = None    #The rootcommander must be set for the function to work!

    def __init__(self,container):
        self.container = container
        if (self.rootcommander is None):
            raise Exception("RootCommander not set!")

    def q(self,cmd):
        r = self.rootcommander.sync_q(cmd)
        if (r!="OK"):
            raise Exception(r)

    def create(self,password,size=64):
        self.q({"cmd": "create","size":size,"container":self.container,"pass":password})
    def open(self,password):
        self.q({"cmd": "open","container":self.container,"pass":password})
    def close(self):
        self.q({"cmd": "close","container":self.container})
    def panic(self):
        self.q({"cmd": "panic","container":self.container})

    #Panic all open containers
    @staticmethod
    def panicall():
        self.q({"cmd": "panic","container":"*"})
