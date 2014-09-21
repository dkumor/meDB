from subprocess32 import Popen,call,PIPE
from uuid import uuid4
import os

class CryptoLuks(object):
    def __init__(self,cryptfile,mountdir,password):
        self.cryptfile = cryptfile
        self.mountdir = mountdir
        self.password = password    #Yes, it keeps the password plainly in memory
        self.fuuid = uuid4().hex    #The UUID used for creating the mapper device
        self.maploc = os.path.join("/dev/mapper",self.fuuid)
        
    def create(self,fsize=64,randomInit=False,owner="root"):
        """Creates a new LUKS container, and mounts it at the given mountpoint.
        Tries to undo changes if there is an error.
        
        Keyword Arguments:
        fsize -- the file size in megabytes (int)
        randomInit -- Whether or not to initialize created file with random bits (bool), takes longer if True.
        """
        
        if (os.path.exists(self.cryptfile)==False):
            if (randomInit==True):
                if (call(["dd","if=/dev/urandom","of="+self.cryptfile,"bs=1M","count="+str(fsize)])!=0):
                    raise IOError("Failed to create file \""+self.cryptfile+"\" (urandom init)")
            else:
                if (call(["fallocate","-l",str(fsize)+"M",self.cryptfile])!=0):
                    raise IOError("Failed to create file \""+self.cryptfile+"\" (fallocate)")
        else:
            raise "File \""+self.cryptfile+"\" already exists!"
            
        if not os.path.exists(self.mountdir):
            os.mkdir(self.mountdir)
        elif (os.listdir(self.mountdir) != []):
            os.remove(self.cryptfile)
            raise IOError("Mount directory \""+self.cryptfile+"\" is not empty!")
        
        #Format the file
        csetup = Popen(["cryptsetup","luksFormat",self.cryptfile],stdin=PIPE)
        csetup.communicate(self.password+"\n")
        csetup.wait()
        if (csetup.returncode != 0):
            os.remove(self.cryptfile)
            os.rmdir(self.mountdir)
            raise IOError("CryptSetup luksFormat failed!")
        
        #Open the volume
        csetup = Popen(["cryptsetup","luksOpen",self.cryptfile,self.fuuid],stdin=PIPE)
        csetup.communicate(self.password+"\n")
        csetup.wait()
        if (csetup.returncode != 0):
            os.remove(self.cryptfile)
            os.rmdir(self.mountdir)
            raise IOError("CryptSetup luksOpen failed!")
        
        if (call(["mkfs.ext4","-j",self.maploc])!= 0):
            call(["cryptsetup","luksClose",self.fuuid])
            os.remove(self.cryptfile)
            os.rmdir(self.mountdir)
            raise IOError("mkfs.ext4 failed!")
        
        if (call(["mount",self.maploc,self.mountdir])!= 0):
            call(["cryptsetup","luksClose",self.fuuid])
            os.remove(self.cryptfile)
            os.rmdir(self.mountdir)
            raise IOError("mount failed!")
        
        #Allows the owner to access the directory and file - since we are currently root
        if (owner!="root"):
            call(["chown",owner,self.mountdir])
            call(["chown",owner,self.cryptfile])
            
        #For security, only owner can even touch the directory.
        call(["chmod","700",self.mountdir])
        
    def open(self):
        """Opens the LUKS file and mounts it"""
        csetup = Popen(["cryptsetup","luksOpen",self.cryptfile,self.fuuid],stdin=PIPE)
        csetup.communicate(self.password+"\n")
        csetup.wait()
        if (csetup.returncode != 0):
            raise IOError("luksOpen failed")
        
        #mount it!
        if ( call(["mount",self.maploc,self.mountdir])!= 0):
            call(["cryptsetup","luksClose",self.fuuid])
            raise IOError("mount failed")
            
    def close(self):
        """Unmounts and closes the LUKS file"""
        self.password = ""
        call(["umount",self.mountdir])
        call(["cryptsetup","luksClose",self.fuuid])
        
        
    def suspend(self):
        """Calls luksSuspend. Stops all IO, and purges keys from kernel. Note that it does not purge the password from this class, so suspend will not guarantee that password is not in memory."""
        call(["cryptsetup","luksSuspend",self.fuuid])
    def resume(self):
        """Resumes previously suspended container"""
        csetup = Popen(["cryptsetup","luksResume",self.fuuid],stdin=PIPE)
        csetup.communicate(self.password+"\n")
        csetup.wait()
        if (csetup.returncode != 0):
            raise IOError("luksResume failed!")
            
    def panic(self):
        """Immediately suspends IO to the volume and attempts closing it. Closing is dependent on processes, while suspend is immediate. Can cause loss of data - use only in emergencies."""
        self.suspend()
        self.close()

if (__name__=="__main__"):
    import time
    c = CryptoLuks("/home/daniel/test.luks","/home/daniel/testingMe","testingTesting")

    t = time.time()
    c.create(owner="daniel")
    print "create:",time.time()-t
    raw_input("ok")
    t= time.time()
    c.close()
    print "close:",time.time()-t
    raw_input("ok")

    c = CryptoLuks("/home/daniel/test.luks","/home/daniel/testingMe","testingTesting")

    t = time.time()
    c.open()
    print "mount:",time.time()-t
    raw_input("ok")
    t= time.time()
    c.suspend()
    print "suspend:",time.time()-t
    raw_input("ok")
    t= time.time()
    c.resume()
    print "resume:",time.time()-t
    raw_input("ok")
    t= time.time()
    c.close()
    print "close:",time.time()-t
    raw_input("done")
