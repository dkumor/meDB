import argparse
import ConfigParser
import os
import logging

def setup(name,extra):
    parser = argparse.ArgumentParser(description="Runs %s service."%(name,))
    #The configuration file to load.
    parser.add_argument("-c","--config",help="The configuration file to use")
    #The following options override values within the configuration file
    parser.add_argument("-l","--logfile",help="The log file location")
    parser.add_argument("-p","--port",help="The port number to launch server on",type=int)
    parser.add_argument("-d","--datadir",help="The root directory for program files.")
    #parser.add_argument("-u","--user",help="Set the username from which to run")
    #parser.add_argument("--key",help="File for root CA private key")
    #parser.add_argument("--cert",help="File for root CA certificate")
    args = parser.parse_args()