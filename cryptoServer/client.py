import requests
import meta

import getpass
import os
import json

class Crypto(object):
    server = 'http://127.0.0.1:'+str(meta.portnumber)+meta.serverKey
    timeout = 60
    
    def __init__(self,filename,mountpoint):
        self.filename = os.path.abspath(filename)
        self.mountpoint = os.path.abspath(mountpoint)
    def q(self,d):
        r=requests.post(self.server,timeout=self.timeout,data=d)
        if (r.status_code!=200):
            raise Exception("Did not get 200 response from server")
        r = json.loads(r.text)
        if (r["result"]!="ok"):
            raise Exception(r["msg"])
        
    def create(self,password,size=64):
        self.q({"cmd": "create","size":size,"container":self.filename,"mountpoint":self.mountpoint,"pass":password,"user":getpass.getuser()})
    def open(self,password):
        self.q({"cmd": "open","container":self.filename,"mountpoint":self.mountpoint,"pass":password})
    def close(self):
        self.q({"cmd": "close","container":self.filename})
    def panic(self):
        self.q({"cmd": "panic","container":self.filename})
    def fuckingPanic(self):
        self.q({"cmd": "panic","container":"*"})
        

if (__name__=="__main__"):
    c = Crypto("rawr2.luks","rawr2")
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
    
