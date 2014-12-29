import sys


from connector.setup.server import ServerSetup
from connector.server.zookeeper import Zookeeper
from connector.server.mongodb import MongoDB
from connector.server.kafkaserver import Kafka
import logging
def runserver():
    s = ServerSetup(description="Connector server",bindir="./bin")

    try:
        zk = Zookeeper(s.hostname,s.port)
        try:
            mg = MongoDB(zk.host,s.hostname)
            kf = Kafka(zk.host,s.hostname)
            print "RUNNING AT",zk.host
            raw_input()
            kf.close()
            mg.close()
        except Exception,e:
            logging.exception(e)
            zk.close()
            raise
        zk.close()
    except:
        s.close()
        raise

    s.close()

def testserver():
    s = ServerSetup(description="Connector server",bindir="./bin")

    try:
        zk = Zookeeper(s.hostname,s.port)
        mg = MongoDB(zk.host,s.hostname,get_open_port())

        print "RUNNING AT",zk.host
        raw_input()

        mg.close()
        zk.close()
    except:
        s.close()
        print sys.exc_info()[0]
        raise
    #s.close() #explicit closing is not needed - on delete it should shut down the server
if (__name__=="__main__"):
    runserver()