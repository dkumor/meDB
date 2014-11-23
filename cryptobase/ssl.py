"""
Key management:
    The database requires a CA certificate and CA key file to function. The certificate and key file
    must be identical for all members of a cluster.

    This CA key is used to generate SSL keys for the server, and to generate SSL keys for all mongoDB databases
"""

from subprocess32 import call
from OpenSSL import crypto, SSL
from random import random
import sys


def generateX509(certfile,keyfile,pubkeyfile=None,
                    cacert = None,cakey=None,
                    cn=None,o=None,
                    keylen = 1024, expiration = 60*60*24*365,
                    isCA=False):

    #First, we generate a key for ourselves
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA,keylen)

    #Next, we create the X509 certificate
    cert = crypto.X509()
    cert.set_version(3)
    cert.set_serial_number(int(random()*sys.maxint))
    if (cn is not None):
        cert.get_subject().CN = cn
    if (o is not None):
        cert.get_subject().O = o

    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(expiration)
    cert.set_pubkey(key)

    if (isCA):
        cert.add_extensions([crypto.X509Extension("basicConstraints", True,"CA:TRUE"),
          crypto.X509Extension("keyUsage", True,"keyCertSign, cRLSign"),
          crypto.X509Extension("subjectKeyIdentifier", False, "hash",subject=cert)])

    #Now we load the certificate authority which will sign our cert.
    #If no certificate authority is given, we self-sign
    ca_cert = cert
    ca_key = key
    if (cacert is not None and cakey is not None):
        #We load the certificates from file
        with open(cacert,"r") as cf:
            ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM,cf.read())
        with open(cakey,"r") as ck:
            ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM,ck.read())

        #Add the authority identifier if there is a parent
        if (isCA):
            cert.add_extensions([crypto.X509Extension("authorityKeyIdentifier",False,"keyid:always",issuer=ca_cert)])


    #Set stuff using the certificate authority
    cert.set_issuer(ca_cert.get_subject())
    cert.sign(ca_key,"sha1")

    #Write the certificate and private/public key to file
    with open(certfile,"wb") as cf:
        cf.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open(keyfile,"wb") as kf:
        kf.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
    if (pubkeyfile is not None):
        #We run the openSSL command to generate the public key file
        call(["openssl","rsa","-in",keyfile,"-pubout","-out",pubkeyfile])

class KeyManager(object):
    def __init__(self,cacert,cakey):
        self.ca_cert = cacert
        self.ca_key = cakey
    #Generate 
    def genkey(self,certfile,keyfile,pubkeyfile=None):
        generateX509(certfile,keyfile,pubkeyfile,self.ca_cert,self.ca_key)
    def genca(self,certfile,keyfile,pubkeyfile=None):
        generateX509(certfile,keyfile,pubkeyfile,self.ca_cert,self.ca_key,isCA=True)

    @staticmethod
    def genRoot(certfile="./ca_cert.pem",keyfile="./ca_key.pem"):
        #Generates a root CA
        generateX509(certfile,keyfile,isCA=True)


if (__name__=="__main__"):
    generateX509("./ca_cert.pem","./ca_key.pem",isCA=True)
    generateX509("./ca2_cert.pem","./ca2_key.pem",cacert="./ca_cert.pem",cakey="./ca_key.pem",isCA=True)
    generateX509("./crt.pem","./key.pem","./pub.pem",cacert="./ca2_cert.pem",cakey="./ca2_key.pem",)
