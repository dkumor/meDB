from subprocess32 import Popen,call,PIPE
import time
import os

def createCrypto(fuuid,password,user="daniel",fsize=64,filedirectory=os.getcwd(),mountdirectory=os.getcwd(),randomInit=False):
    cryptfile = os.path.join(filedirectory,fuuid+".luks")
    mountdir = os.path.join(mountdirectory,fuuid)
    maploc = os.path.join("/dev/mapper",fuuid)
    
    #Create the file
    if (randomInit==False):
        #Simply allocate a file
        code = call(["fallocate","-l",str(fsize)+"M",cryptfile])
    else:
        #Create the file filling it with 0s
        call(["dd","if=/dev/urandom","of="+cryptfile,"bs=1M","count="+str(fsize)])
    
    #Make the mount directory
    os.mkdir(mountdir)
    
    #Set up the file
    csetup = Popen(["cryptsetup","luksFormat",cryptfile],
                stdin=PIPE)
    csetup.communicate(password+"\n")
    csetup.wait()
    
    #Open the volume
    csetup = Popen(["cryptsetup","luksOpen",cryptfile,fuuid],
                stdin=PIPE)
    csetup.communicate(password+"\n")
    csetup.wait()
    
    #Make the filesystem ext4
    code = call(["mkfs.ext4","-j",maploc])
    
    print code
    
    #Mount it!
    code = call(["mount",maploc,mountdir])
    
    print code
    
    #Set the folder permissions to the user!
    code = call(["chown",user+":"+user,mountdir])
    
    print code
    
    code = call(["chmod","700",mountdir])
    print code
    
def mountCrypto(fuuid,password,filedirectory=os.getcwd(),mountdirectory=os.getcwd()):
    cryptfile = os.path.join(filedirectory,fuuid+".luks")
    mountdir = os.path.join(mountdirectory,fuuid)
    maploc = os.path.join("/dev/mapper",fuuid)
    
    #Open the volume
    csetup = Popen(["cryptsetup","luksOpen",cryptfile,fuuid],
                stdin=PIPE)
    csetup.communicate(password+"\n")
    csetup.wait()
    
    #Mount it!
    code = call(["mount",maploc,mountdir])
def suspendCrypto(fuuid):
    print call(["cryptsetup","luksSuspend",fuuid])
def resumeCrypto(fuuid,password):
    csetup = Popen(["cryptsetup","luksResume",fuuid],
                stdin=PIPE)
    csetup.communicate(password+"\n")
    csetup.wait()
    
def unmountCrypto(fuuid,mountdirectory=os.getcwd()):
    mountdir = os.path.join(mountdirectory,fuuid)
    
    code = call(["umount",mountdir])
    print code
    
    print call(["cryptsetup","luksClose",fuuid])
#createCrypto("r24rwe23r","testingtesting123",fsize="64M")
fuuid = "testcrypt"
pwn = "testingtesting123"

t = time.time()
createCrypto(fuuid,pwn)
print "create:",time.time()-t
raw_input("ok")
t= time.time()
unmountCrypto(fuuid)
print "umount:",time.time()-t
raw_input("ok")
t = time.time()
mountCrypto(fuuid,pwn)
print "mount:",time.time()-t
raw_input("ok")
t= time.time()
suspendCrypto(fuuid)
print "suspend:",time.time()-t
raw_input("suspended")
t= time.time()
resumeCrypto(fuuid,pwn)
print "resume:",time.time()-t
raw_input("ok")
t= time.time()
unmountCrypto(fuuid)
print "umount:",time.time()-t
raw_input("done")
