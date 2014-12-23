"""
Allows for adding/deleting users at will
"""

import os,pwd,grp
from subprocess32 import call

def drop_privileges(username):

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(username).pw_uid
    running_gid = grp.getgrnam(username).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    old_umask = os.umask(077)

def mkusr(username):
    #Creates the given user
    call(["useradd","-M","-r","-s","/bin/false","-c","Robot user",username])

def delusr(username):
    #Deletes the user
    call(["userdel",username])

def userexists(username):
    #Returns True if user exists, and False if user does not exist
    return call(["id",username])==0

if (__name__=="__main__"):
    assert userexists("testuser") == False
    mkusr("testuser")
    assert userexists("testuser") == True
    delusr("testuser")
    assert userexists("testuser") == False
