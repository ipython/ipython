# encoding: utf-8

"""Pickle related utilities."""

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
from twisted.python import log

class CannedObject(object):
    pass
    
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
    else:
        return obj

def canDict(obj):
    if isinstance(obj, dict):
        for k, v in obj.iteritems():
            obj[k] = can(v)
        return obj
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
    else:
        return obj

def uncanDict(obj, g=None):
    if isinstance(obj, dict):
        for k, v in obj.iteritems():
            obj[k] = uncan(v,g)
        return obj
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
