# encoding: utf-8
# -*- test-case-name: IPython.kernel.test.test_newserialized -*-

"""Refactored serialization classes and interfaces."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import cPickle as pickle

from zope.interface import Interface, implements
from twisted.python import components

try:
    import numpy
except ImportError:
    pass

from IPython.kernel.error import SerializationError

class ISerialized(Interface):
    
    def getData():
        """"""

    def getDataSize(units=10.0**6):
        """"""

    def getTypeDescriptor():
        """"""

    def getMetadata():
        """"""
        
        
class IUnSerialized(Interface):
    
    def getObject():
        """"""
        
class Serialized(object):
    
    implements(ISerialized)
    
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
    
    implements(IUnSerialized)
        
    def __init__(self, obj):
        self.obj = obj
        
    def getObject(self):
        return self.obj

        
class SerializeIt(object):
    
    implements(ISerialized)
    
    def __init__(self, unSerialized):
        self.data = None
        self.obj = unSerialized.getObject()
        if globals().has_key('numpy'):
            if isinstance(self.obj, numpy.ndarray):
                if len(self.obj) == 0:         # length 0 arrays can't be reconstructed
                    raise SerializationError("You cannot send a length 0 array")
                self.obj = numpy.ascontiguousarray(self.obj, dtype=None)
                self.typeDescriptor = 'ndarray'
                self.metadata = {'shape':self.obj.shape,
                                 'dtype':self.obj.dtype.str}
            else:
                self.typeDescriptor = 'pickle'
                self.metadata = {}
        else:
            self.typeDescriptor = 'pickle'
            self.metadata = {}
        self._generateData()            
    
    def _generateData(self):
        if self.typeDescriptor == 'ndarray':
            self.data = numpy.getbuffer(self.obj)
        elif self.typeDescriptor == 'pickle':
            self.data = pickle.dumps(self.obj, 2)
        else:
            raise SerializationError("Really wierd serialization error.")
        del self.obj
        
    def getData(self):
        return self.data
        
    def getDataSize(self, units=10.0**6):
        return len(self.data)/units
        
    def getTypeDescriptor(self):
        return self.typeDescriptor
        
    def getMetadata(self):
        return self.metadata


class UnSerializeIt(UnSerialized):
    
    implements(IUnSerialized)
    
    def __init__(self, serialized):
        self.serialized = serialized
        
    def getObject(self):
        typeDescriptor = self.serialized.getTypeDescriptor()
        if globals().has_key('numpy'):
            if typeDescriptor == 'ndarray':
                result = numpy.frombuffer(self.serialized.getData(), dtype = self.serialized.metadata['dtype'])
                result.shape = self.serialized.metadata['shape']
                # This is a hack to make the array writable.  We are working with
                # the numpy folks to address this issue.
                result = result.copy()
            elif typeDescriptor == 'pickle':
                result = pickle.loads(self.serialized.getData())
            else:
                raise SerializationError("Really wierd serialization error.")
        elif typeDescriptor == 'pickle':
            result = pickle.loads(self.serialized.getData())
        else:
            raise SerializationError("Really wierd serialization error.")
        return result

components.registerAdapter(UnSerializeIt, ISerialized, IUnSerialized)

components.registerAdapter(SerializeIt, IUnSerialized, ISerialized)
    
def serialize(obj):
    return ISerialized(UnSerialized(obj))
    
def unserialize(serialized):
    return IUnSerialized(serialized).getObject()
