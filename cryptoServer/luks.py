from subprocess32 import Popen,call,PIPE
import os

def createCrypto(fuuid,password,user="daniel",fsize="125M",filedirectory=os.getcwd(),mountdirectory=os.getcwd()):
    cryptfile = os.path.join(filedirectory,fuuid+".luks")
    mountdir = os.path.join(mountdirectory,fuuid)
    
    #Create the file and make mount directory
    code = call(["fallocate","-l",fsize,cryptfile])
    os.mkdir(mountdir)
    
    #Set up the file
    csetup = Popen(["cryptsetup","-y","luksFormat",cryptfile],
                stdin=PIPE)
    csetup.communicate("YES\n"+password+"\n")
    csetup.wait()
    
    #Open the volume
    csetup = Popen(["cryptsetup","-y","luksOpen",cryptfile,fuuid],
                stdin=PIPE)
    csetup.communicate("YES\n"+password+"\n")
    csetup.wait()
    
    print code
def unmountCrypto(fuuid,mountdirectory=os.getcwd()):
    mountdir = os.path.join(mountdirectory,fuuid)
    
    
createCrypto("r24rwer23r","testingtesting123",fsize="64M")
raw_input("ok")
unmountCrypto("r24rwer23r")
