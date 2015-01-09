import sys
import signal

from connector.setup.server import ServerSetup
from connector.server.zookeeper import Zookeeper
from connector.server.mongodb import MongoDB
from connector.server.kafkaserver import Kafka


def runserver():
    s = ServerSetup(description="Connector server",bindir="./bin")
    zk = Zookeeper(s.hostname,s.port)
    mg = MongoDB(zk.host,s.hostname)
    kf = Kafka(zk.host,s.hostname)

    

    print "RUNNING AT",zk.host
    
    while (True):
        try:
            signal.pause()
        except KeyboardInterrupt:
            print "CLOSING"
            kf.close()
            mg.close()
            zk.close()
            s.close()
    #s.close() #explicit closing is not needed - on delete it should shut down the server


if (__name__=="__main__"):
    runserver()