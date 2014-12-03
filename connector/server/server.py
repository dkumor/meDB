from zoo import ZooConnection

from functools import partial

class ZooServer(ZooConnection):
    def __init__(self,dbfolder,rootpath="/connector",jardir="../jar/",logger=None):
        ZooConnection.__init__(self,dbfolder,jardir,logger)
        self.rootpath = rootpath
        #Create the rootpath, and the pathway for individual databases
        self.client.ensure_path(rootpath+"/db")

        #We save the root pathway
        self.rootchildren = set([u'db'])

        #Children of location
        self.locchildren = {}

        #Set up client to be listening for all changes/connections/disconnections
        self.client.ChildrenWatch(rootpath,self.watchRootChildren)

    def watchRootChildren(self,children):
        children = set(children)
        
        #For any new nodes added
        for i in (children - self.rootchildren):
            #Add watcher for the node
            logger.info("Adding root node %s"%(i,))
            loc = self.rootpath+"/"+i

            self.locchildren[loc] = set([])
            self.client.ChildrenWatch(loc,partial(self.watchChild,loc))

        self.rootchildren = children

    def watchChild(self,loc,children):
        children= set(children)

        #For any new nodes added
        for i in (children - self.locchildren[loc]):
            l2 = loc + "/"+i
            logging.info("New client connected: %s"%(l2,))
            self.client.DataWatch(l2+"/isconnected",partial(self.watchcNode,l2))

        self.locchildren[loc] = children

    def watchcNode(self,loc,data,stat,event):
        if (data is None and stat is None and event is None):
            self.client.delete(loc,recursive=True)
            print "DELETING",loc

if (__name__=="__main__"):
    import shutil
    import os
    import time


    if (os.path.exists("./tmp")):
        shutil.rmtree("./tmp")

    os.makedirs("./tmp")

    from server import ZooServer

    import logging
    logging.basicConfig()

    zooc = ZooServer("./tmp")

    print "Running Server at port",zooc.port

    raw_input()

    zooc.close()