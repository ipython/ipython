# encoding: utf-8

"""Pickle related utilities. Perhaps this should be called 'can'."""

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

from types import FunctionType

# contents of codeutil should either be in here, or codeutil belongs in IPython/util
from IPython.zmq.parallel.dependency import dependent
import codeutil

class CannedObject(object):
    def __init__(self, obj, keys=[]):
        self.keys = keys
        self.obj = obj
        for key in keys:
            setattr(obj, key, can(getattr(obj, key)))
            
    
    def getObject(self, g=None):
        if g is None:
            g = globals()
        for key in self.keys:
            setattr(self.obj, key, uncan(getattr(self.obj, key), g))
        return self.obj

        

class CannedFunction(CannedObject):
    
    def __init__(self, f):
        self._checkType(f)    
        self.code = f.func_code
    
    def _checkType(self, obj):
        assert isinstance(obj, FunctionType), "Not a function type"
    
    def getFunction(self, g=None):
        if g is None:
            g = globals()
        newFunc = FunctionType(self.code, g)
        return newFunc

def can(obj):
    if isinstance(obj, FunctionType):
        return CannedFunction(obj)
    elif isinstance(obj, dependent):
        keys = ('f','df')
        return CannedObject(obj, keys=keys)
    elif isinstance(obj,dict):
        return canDict(obj)
    elif isinstance(obj, (list,tuple)):
        return canSequence(obj)
    else:
        return obj

def canDict(obj):
    if isinstance(obj, dict):
        newobj = {}
        for k, v in obj.iteritems():
            newobj[k] = can(v)
        return newobj
    else:
        return obj

def canSequence(obj):
    if isinstance(obj, (list, tuple)):
        t = type(obj)
        return t([can(i) for i in obj])
    else:
        return obj

def uncan(obj, g=None):
    if isinstance(obj, CannedFunction):
        return obj.getFunction(g)
    elif isinstance(obj, CannedObject):
        return obj.getObject(g)
    elif isinstance(obj,dict):
        return uncanDict(obj)
    elif isinstance(obj, (list,tuple)):
        return uncanSequence(obj)
    else:
        return obj

def uncanDict(obj, g=None):
    if isinstance(obj, dict):
        newobj = {}
        for k, v in obj.iteritems():
            newobj[k] = uncan(v,g)
        return newobj
    else:
        return obj

def uncanSequence(obj, g=None):
    if isinstance(obj, (list, tuple)):
        t = type(obj)
        return t([uncan(i,g) for i in obj])
    else:
        return obj


def rebindFunctionGlobals(f, glbls):
    return FunctionType(f.func_code, glbls)
