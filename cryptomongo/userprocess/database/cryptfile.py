"""
The Crypto object: it wraps the rootcommander object
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
    def fuckingPanic(self):
        self.q({"cmd": "panic","container":"*"})


if (__name__=="__main__"):
    c = FileCrypto("rawr2")
    c.open("rawr")
    raw_input(">>>")
    c.fuckingPanic()
    raw_input(">>>")
    c.open("rawr")
    raw_input(">>>")
    c.panic()
    raw_input(">>>")
    c.open("rawr")
    raw_input(">>>")
    c.close()
