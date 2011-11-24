# encoding: utf-8

"""Pickle related utilities. Perhaps this should be called 'can'."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import copy
import sys
from types import FunctionType

import codeutil

#-------------------------------------------------------------------------------
# Classes
#-------------------------------------------------------------------------------


class CannedObject(object):
    def __init__(self, obj, keys=[]):
        self.keys = keys
        self.obj = copy.copy(obj)
        for key in keys:
            setattr(self.obj, key, can(getattr(obj, key)))


    def getObject(self, g=None):
        if g is None:
            g = globals()
        for key in self.keys:
            setattr(self.obj, key, uncan(getattr(self.obj, key), g))
        return self.obj

class Reference(CannedObject):
    """object for wrapping a remote reference by name."""
    def __init__(self, name):
        if not isinstance(name, basestring):
            raise TypeError("illegal name: %r"%name)
        self.name = name

    def __repr__(self):
        return "<Reference: %r>"%self.name

    def getObject(self, g=None):
        if g is None:
            g = globals()
        try:
            return g[self.name]
        except KeyError:
            raise NameError("name %r is not defined"%self.name)


class CannedFunction(CannedObject):

    def __init__(self, f):
        self._checkType(f)
        self.code = f.func_code
        self.defaults = f.func_defaults
        self.module = f.__module__ or '__main__'
        self.__name__ = f.__name__

    def _checkType(self, obj):
        assert isinstance(obj, FunctionType), "Not a function type"

    def getObject(self, g=None):
        # try to load function back into its module:
        if not self.module.startswith('__'):
            try:
                __import__(self.module)
            except ImportError:
                pass
            else:
                g = sys.modules[self.module].__dict__

        if g is None:
            g = globals()
        newFunc = FunctionType(self.code, g, self.__name__, self.defaults)
        return newFunc

#-------------------------------------------------------------------------------
# Functions
#-------------------------------------------------------------------------------

def can(obj):
    # import here to prevent module-level circular imports
    from IPython.parallel import dependent
    if isinstance(obj, dependent):
        keys = ('f','df')
        return CannedObject(obj, keys=keys)
    elif isinstance(obj, FunctionType):
        return CannedFunction(obj)
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
    if isinstance(obj, CannedObject):
        return obj.getObject(g)
    elif isinstance(obj,dict):
        return uncanDict(obj, g)
    elif isinstance(obj, (list,tuple)):
        return uncanSequence(obj, g)
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
