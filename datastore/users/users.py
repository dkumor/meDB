
"""
The User is really a cheap abstraction for inputs and outputs. Rather than have an individual document
for each input and each output, we group them by users. That way, a device that connects has all its properties
associated with one document, and it becomes trivial to modify/check its properties and valid input types.
This also means that users are very, very cheap - each item can be its own user. A heart rate sensor is one user,
and an android app is another - and each user can have multiple inputs and outputs that it defines.

This architecture choice has two benefits: Usually, a sensor defines specific inputs which are somehow related
to each other. This means that correlations and compression of data is more likely to be effective with all the 
inputs of one user. Secondly, having all of a user's IO defined in one document, it becomes trivial to check for
validity of input

The user data structure is as follows:

_id: the uid
secret: The "password" which gives access to the uid

perm:   The permissions  of this user with respect to other users
        {
            uid: {
                r: Read data that the user wrote (including things it triggered, and its registered inputs/outputs)
                o: Trigger the user's outputs
                p: Read the user's permissions
                s: Read the user's secret
                wp: Write user's permissions (can only enable permissions it itself has)
                ws: Write the user's secret
                wr: Write the user's registered inputs (ie, allows another user to register inputs)
                wo: Write the user's outputs (ie, allows another user to create/modify outputs)
                d: Can delete user
            }
        }
        1) "db" - sets permissions database-wide (admin has db.<everything>=True)
        2) uid - sets permissions for the given uid

write: T/F : Whether or not allowed to write _data_ to the database
wunreg: If write is true, then:
            -1 : User is not allowed to write unregistered inputs to the database
            <any other number>: The kafka partition number that unregistered inputs are written to.

create: T/F : Whether or not allowed to create user. The new user can only have permissions <= creating user

trigger: [] : Specific IDs of outputs that the user is allowed to trigger. This is similar to the 'o' permission,
        but here, it is not per-user, but rather a specific list of outputs

inputs: The inputs to the database that the uid registers. In general, inputs do not need to be registered, and can be
        of any type. A registered input is constrained to within the registered type/range. It allows analysis
        algorithms to normalize and process the data. Registering inputs also allows easy finding of the most common inputs


outputs: The outputs from the database that the uid registers. Outputs require registration.

Inputs and outputs have data of the following format:

[
    {
        id: The Kafka partition number to which this input/output is written to
        parts: {
            partname: {metadata}
        }
        meta: {metadata}
    }
]


"""



class Users(object):
    """
        Given a mongoDB database object, opens the collection
    """
    def __init__(self,db,name="users"):
        self.p = db[name]

    def __call__(self,uid,secret):
        #Given uid and secret, returns the user object
        res = self.p.find_one({"_id": ObjectId(uid),"secret": secret})
        if (res!=None):
            return usr(res,self.p)
        return None

    def get(self,uid):
        if not ObjectId.is_valid(uid): return None
        #Gets user based on uid
        res = self.p.find_one({"_id": ObjectId(uid)})
        if (res!=None):
            return usr(res,self.p)
        return None

    def create(self,uid=None,secret=None,perm = {},write = False,create=False,outputs=[]):
        if (uid==None):
            uid = uuid.uuid4().hex[:24]
        else:
            if not ObjectId.is_valid(uid): return None
        if (secret==None):
            secret = uuid.uuid4().hex
        r = self.p.insert({"_id": ObjectId(uid),"secret": secret,"perm": perm,"write": write,"create": create,
                    "outputs": outputs, "inputs":{}})
        return usr(self.p.find_one({"_id": r}),self.p)



if (__name__=="__main__"):
    import shutil
    import os
    from database.mongo import Connection

    testname = "./test_db"
    if (os.path.exists(testname)):
        shutil.rmtree(testname)

    os.mkdir(testname)
    c = Connection(testname)

    p = Users(c.cursor().db)

    assert p(uuid.uuid4().hex[:24],"fdfsfsd")==None
    assert p.get(uuid.uuid4().hex[:24])==None

    e = p.create(write=False,create=True)

    f = p.get(e.id)

    assert e==f

    assert f.pRead("safdfsad") == False
    f.pRead("safdfsad",True)
    f.pReadOut("safdfsad",True)

    assert f.write == False
    assert f.create == True
    assert f.pRead("safdfsad")==True
    assert f.pReadOut("safdfsad")==True
    assert f.pReadPerm("safdfsad")==False

    assert f.secret == e.secret
    f.secret = "hlop"
    assert f.secret == "hlop"
    assert f.pRead("testing") == False

    f.pRead("safdfsad",False)

    assert f.pRead("db") ==False
    assert f.pRead("safdfsad")==False
    f.pRead("aardvark",True)
    f.pRead("trolo",True)
    assert f.pRead("aardvark")==True


    f.write = True
    f.create = False
    assert f.write==True
    assert f.create == False

    #Now test the inputs
    assert len(f.inputlist())==0

    assert f.getInput("hi")==None

    f.addInput("hello")
    f.addInput("world",{"gg":4,"ho": ["fg",33]})
    f.addInput("dude",{"foo":"bar"})

    assert len(f.inputlist())==3
    assert f.getInput("hello")!=None
    assert f.getInput("world")["ho"][1]==33
    assert f.getInput("dude")["foo"]=="bar"

    f.setInput("dude",{"gram":3})

    assert not ("foo" in f.getInput("dude"))
    assert f.getInput("dude")["gram"]==3

    f.remInput("dude")

    assert f.getInput("dude") == None

    g = p(f.id,f.secret)

    assert f == g
    assert g.secret == "hlop"
    assert g.write == True
    assert g.pRead("safdfsad")==False
    assert g.pRead("aardvark")==True
    assert g.pRead("trolo") ==True
    g.pRead("trolo",False)
    assert g.pRead("trolo") == False
    assert g.pReadOut("safdfsad")==True

    g.pReadOut("safdfsad",False)

    assert g.pReadOut("safdfsad")==False

    assert len(g.inputlist())==2
    assert g.getInput("hello")!=None
    assert g.getInput("world")["ho"][1]==33
    assert g.getInput("dude")==None

    g.addInput("ra",{"men":"yum"})

    assert g.getInput("ra")["men"]=="yum"

    assert g.input("ra",getv={"men":None,'dudes': None})["men"]=="yum"
    assert g.input("ra",getv={"men":None,'dudes': 1})["dudes"]==None
    g.input("ra",setv={"men": "pf","dudes": 1337})

    assert g.input("ra",getv={"men":None,'dudes': None})["men"]=="pf"
    assert g.input("ra",getv={"men":None,'dudes': 1})["dudes"]==1337

    i = f.id
    c.close()
    c = Connection(testname)

    q = Users(c.cursor().db)

    h = q(i,"hlop")
    assert h != None
    assert h.secret == "hlop"
    assert h.write == True
    assert h.pRead("safdfsad")==False
    assert h.pRead("aardvark")==True
    assert h.pRead("trolo") == False

    assert len(h.inputlist())==3
    assert h.getInput("hello")!=None
    assert h.getInput("world")["ho"][1]==33
    assert h.getInput("dude")==None


    assert h.input("ra",getv={"men":None,'dudes': None})["men"]=="pf"
    assert h.input("ra",getv={"men":None,'dudes': 1})["dudes"]==1337

    assert q.get(uuid.uuid4().hex[:24])==None
    h.delete()

    assert q.get(i)==None

    assert q.get("hello") == None

    c.close()

    shutil.rmtree(testname)

    print "\n\nAll tests completed successfully\n"
