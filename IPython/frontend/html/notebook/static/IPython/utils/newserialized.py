# encoding: utf-8
# -*- test-case-name: IPython.kernel.test.test_newserialized -*-

"""Refactored serialization classes and interfaces."""

__docformat__ = "restructuredtext en"

# Tell nose to skip this module
__test__ = {}

#-------------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import sys
import cPickle as pickle

try:
    import numpy
except ImportError:
    numpy = None

class SerializationError(Exception):
    pass

if sys.version_info[0] >= 3:
    buffer = memoryview
    py3k = True
else:
    py3k = False
    if sys.version_info[:2] <= (2,6):
        memoryview = buffer

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class ISerialized:
    
    def getData():
        """"""

    def getDataSize(units=10.0**6):
        """"""

    def getTypeDescriptor():
        """"""

    def getMetadata():
        """"""
        
        
class IUnSerialized:
    
    def getObject():
        """"""
        
class Serialized(object):
    
    # implements(ISerialized)
    
    def __init__(self, data, typeDescriptor, metadata={}):
        self.data = data
        self.typeDescriptor = typeDescriptor
        self.metadata = metadata
        
    def getData(self):
        return self.data
        
    def getDataSize(self, units=10.0**6):
        return len(self.data)/units
        
    def getTypeDescriptor(self):
        return self.typeDescriptor
        
    def getMetadata(self):
        return self.metadata

        
class UnSerialized(object):
    
    # implements(IUnSerialized)
        
    def __init__(self, obj):
        self.obj = obj
        
    def getObject(self):
        return self.obj

        
class SerializeIt(object):
    
    # implements(ISerialized)
    
    def __init__(self, unSerialized):
        self.data = None
        self.obj = unSerialized.getObject()
        if numpy is not None and isinstance(self.obj, numpy.ndarray):
            if len(self.obj.shape) == 0: # length 0 arrays are just pickled
                self.typeDescriptor = 'pickle'
                self.metadata = {}
            else:
                self.obj = numpy.ascontiguousarray(self.obj, dtype=None)
                self.typeDescriptor = 'ndarray'
                self.metadata = {'shape':self.obj.shape,
                                 'dtype':self.obj.dtype}
        elif isinstance(self.obj, bytes):
            self.typeDescriptor = 'bytes'
            self.metadata = {}
        elif isinstance(self.obj, buffer):
            self.typeDescriptor = 'buffer'
            self.metadata = {}
        else:
            self.typeDescriptor = 'pickle'
            self.metadata = {}
        self._generateData()
    
    def _generateData(self):
        if self.typeDescriptor == 'ndarray':
            self.data = buffer(self.obj)
        elif self.typeDescriptor in ('bytes', 'buffer'):
            self.data = self.obj
        elif self.typeDescriptor == 'pickle':
            self.data = pickle.dumps(self.obj, -1)
        else:
            raise SerializationError("Really wierd serialization error.")
        del self.obj
        
    def getData(self):
        return self.data
        
    def getDataSize(self, units=10.0**6):
        return 1.0*len(self.data)/units
        
    def getTypeDescriptor(self):
        return self.typeDescriptor
        
    def getMetadata(self):
        return self.metadata


class UnSerializeIt(UnSerialized):
    
    # implements(IUnSerialized)
    
    def __init__(self, serialized):
        self.serialized = serialized
        
    def getObject(self):
        typeDescriptor = self.serialized.getTypeDescriptor()
        if numpy is not None and typeDescriptor == 'ndarray':
                buf = self.serialized.getData()
                if isinstance(buf, (bytes, buffer, memoryview)):
                    result = numpy.frombuffer(buf, dtype = self.serialized.metadata['dtype'])
                else:
                    raise TypeError("Expected bytes or buffer/memoryview, but got %r"%type(buf))
                result.shape = self.serialized.metadata['shape']
        elif typeDescriptor == 'pickle':
            result = pickle.loads(self.serialized.getData())
        elif typeDescriptor in ('bytes', 'buffer'):
            result = self.serialized.getData()
        else:
            raise SerializationError("Really wierd serialization error.")
        return result

def serialize(obj):
    return SerializeIt(UnSerialized(obj))
    
def unserialize(serialized):
    return UnSerializeIt(serialized).getObject()
