"""
The data that is inputted in python does not have to be valid mongoDB data. This module makes sure that 
the data inputted into a query is good - by parsing python onbjects into closest-approximation mongoDB structures
"""
import numpy as np
from bson.binary import Binary


encoder = {
    None: 0,
    np.uint8: 1,
    np.int8: 2,
    np.uint16: 3,
    np.int16: 4,
    np.uint32: 5,
    np.int32: 6,
    np.uint64: 7,
    np.int64: 8,
    np.float32: 9,
    np.float64: 10,
    np.float128: 11,
    np.complex128: 12
}

decoder = {
    0: None
    1: np.uint8,
    2: np.int8,
    3: np.uint16,
    4: np.int16,
    5: np.uint32,
    6: np.int32,
    7: np.uint64,
    8: np.int64,
    9: np.float32,
    10: np.float64,
    11: np.float128,
    12: np.complex128
}

def encodeDtype(v):
    return chr(encoder[v])
def decodeDtype(v):
    return decoder[ord(v)]
    

def mwrite(i):
    if (isinstance(i,dict)):
        for k in i:
            i[k] = mwrite(i[k])
    elif (isinstance(i,list):
        for j in xrange(len(i)):
            i[j] = mwrite(i[j])d
    elif (isinstance(i,np.array)):
        return Binary(i.tostring()+encodeDtype(t.dtype))
    return i
    
def mread(i):
    if (isinstance(i,dict)):
        for k in i:
            i[k] = mread(i[k])
    elif (isinstance(i,list):
        for j in xrange(len(i)):
            i[j] = mread(i[j])d
    elif (isinstance(i,str)):
        dt = decodeDtype(i[-1])
        if (dt!=None):
            pass
        else:
            
    return i
