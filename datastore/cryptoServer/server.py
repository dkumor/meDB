import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cryptoServer")

import tornado.web
import tornado.ioloop
import json

import signal

#Right now all that is supported is luks. Perhaps someday bitlocker or truecrypt will also be implemented.
import luks

import meta

class cryptoServer(tornado.web.RequestHandler):
    containers = {}
    def post(self):
        d = {}
        try:
            d = {
                "cmd": self.get_argument("cmd"),
                "container": self.get_argument("container")
            }
            cmd = d["cmd"]
            if (cmd=="create"):
                d["size"] = int(self.get_argument("size"))
                d["mountpoint"] = self.get_argument("mountpoint")
                d["user"] = self.get_argument("user")
                logger.info("Create %(container)s (%(size)sM,%(user)s)-> %(mountpoint)s",d)
                if (d['container'] in self.containers):
                    raise Exception("Container already open")
                lcntnr= luks.CryptoLuks(d["container"],d["mountpoint"])
                lcntnr.create(self.get_argument("pass"),owner=d["user"],fsize=d["size"])
                self.containers[d['container']] = lcntnr
            elif (cmd=="close"):
                logger.info("Close %(container)s",d)
                if (d["container"] in self.containers):
                    self.containers[d["container"]].close()
                    del self.containers[d["container"]]
            elif (cmd=="open"):
                d["mountpoint"] = self.get_argument("mountpoint")
                logger.info("Open %(container)s -> %(mountpoint)s",d)
                if (d['container'] in self.containers):
                    raise Exception("Container already in use")
                lcntnr = luks.CryptoLuks(d["container"],d["mountpoint"])
                lcntnr.open(self.get_argument("pass"))
                self.containers[d['container']] = lcntnr
            elif (cmd=="panic"):
                if (d["container"]=="*"):
                    logger.critical("TOTAL PANIC - HOLY FUCKING SHIT, WE'RE FUCKED")
                    for k in self.containers:
                        self.containers[k].panic()
                    self.containers.clear()
                    logger.warning("All containers closed.")
                    
                else:
                    if (d['container'] in self.containers):
                        logger.warning(" %(container)s - PANIC",d)
                        self.containers[d["container"]].panic()
                        del self.containers[d["container"]]
                        logger.warning(" %(container)s - closed",d)
            self.write(json.dumps({"result": "ok"}))
        except Exception, e:
            logger.error("Error: "+str(e))
            self.write(json.dumps({"result": "fail","msg":str(e)}))
def shutdown_server():
    tornado.ioloop.IOLoop.instance().stop()
def clearMounts(a,b):
    print "Shutting down server"
    tornado.ioloop.IOLoop.instance().add_callback_from_signal(shutdown_server)
    print "Closing all open containers..."
    for k in cryptoServer.containers:
        cryptoServer.containers[k].panic()
    cryptoServer.containers.clear()

if (__name__=="__main__"):
    signal.signal(signal.SIGINT, clearMounts)
    
    cServer = tornado.web.Application([(meta.serverKey,cryptoServer),])
    cServer.listen(meta.portnumber,address='127.0.0.1')
    logging.info("CryptoServer running on port %s",meta.portnumber,extra={"cmd":"","container":""})
    tornado.ioloop.IOLoop.instance().start()