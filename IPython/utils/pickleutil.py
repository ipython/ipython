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
import logging
import sys
from types import FunctionType

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import numpy
except:
    numpy = None

import py3compat
from importstring import import_item

from IPython.config import Application

if py3compat.PY3:
    buffer = memoryview
    class_type = type
else:
    from types import ClassType
    class_type = (type, ClassType)

#-------------------------------------------------------------------------------
# Classes
#-------------------------------------------------------------------------------


class CannedObject(object):
    def __init__(self, obj, keys=[], hook=None):
        """can an object for safe pickling
        
        Parameters
        ==========
        
        obj:
            The object to be canned
        keys: list (optional)
            list of attribute names that will be explicitly canned / uncanned
        hook: callable (optional)
            An optional extra callable,
            which can do additional processing of the uncanned object.
        
        large data may be offloaded into the buffers list,
        used for zero-copy transfers.
        """
        self.keys = keys
        self.obj = copy.copy(obj)
        self.hook = can(hook)
        for key in keys:
            setattr(self.obj, key, can(getattr(obj, key)))
        
        self.buffers = []

    def get_object(self, g=None):
        if g is None:
            g = {}
        obj = self.obj
        for key in self.keys:
            setattr(obj, key, uncan(getattr(obj, key), g))
        
        if self.hook:
            self.hook = uncan(self.hook, g)
            self.hook(obj, g)
        return self.obj
    

class Reference(CannedObject):
    """object for wrapping a remote reference by name."""
    def __init__(self, name):
        if not isinstance(name, basestring):
            raise TypeError("illegal name: %r"%name)
        self.name = name
        self.buffers = []

    def __repr__(self):
        return "<Reference: %r>"%self.name

    def get_object(self, g=None):
        if g is None:
            g = {}
        
        return eval(self.name, g)


class CannedFunction(CannedObject):

    def __init__(self, f):
        self._check_type(f)
        self.code = f.func_code
        if f.func_defaults:
            self.defaults = [ can(fd) for fd in f.func_defaults ]
        else:
            self.defaults = None
        self.module = f.__module__ or '__main__'
        self.__name__ = f.__name__
        self.buffers = []

    def _check_type(self, obj):
        assert isinstance(obj, FunctionType), "Not a function type"

    def get_object(self, g=None):
        # try to load function back into its module:
        if not self.module.startswith('__'):
            __import__(self.module)
            g = sys.modules[self.module].__dict__

        if g is None:
            g = {}
        if self.defaults:
            defaults = tuple(uncan(cfd, g) for cfd in self.defaults)
        else:
            defaults = None
        newFunc = FunctionType(self.code, g, self.__name__, defaults)
        return newFunc

class CannedClass(CannedObject):

    def __init__(self, cls):
        self._check_type(cls)
        self.name = cls.__name__
        self.old_style = not isinstance(cls, type)
        self._canned_dict = {}
        for k,v in cls.__dict__.items():
            if k not in ('__weakref__', '__dict__'):
                self._canned_dict[k] = can(v)
        if self.old_style:
            mro = []
        else:
            mro = cls.mro()
        
        self.parents = [ can(c) for c in mro[1:] ]
        self.buffers = []

    def _check_type(self, obj):
        assert isinstance(obj, class_type), "Not a class type"

    def get_object(self, g=None):
        parents = tuple(uncan(p, g) for p in self.parents)
        return type(self.name, parents, uncan_dict(self._canned_dict, g=g))

class CannedArray(CannedObject):
    def __init__(self, obj):
        self.shape = obj.shape
        self.dtype = obj.dtype.descr if obj.dtype.fields else obj.dtype.str
        if sum(obj.shape) == 0:
            # just pickle it
            self.buffers = [pickle.dumps(obj, -1)]
        else:
            # ensure contiguous
            obj = numpy.ascontiguousarray(obj, dtype=None)
            self.buffers = [buffer(obj)]
    
    def get_object(self, g=None):
        data = self.buffers[0]
        if sum(self.shape) == 0:
            # no shape, we just pickled it
            return pickle.loads(data)
        else:
            return numpy.frombuffer(data, dtype=self.dtype).reshape(self.shape)


class CannedBytes(CannedObject):
    wrap = bytes
    def __init__(self, obj):
        self.buffers = [obj]
    
    def get_object(self, g=None):
        data = self.buffers[0]
        return self.wrap(data)

def CannedBuffer(CannedBytes):
    wrap = buffer

#-------------------------------------------------------------------------------
# Functions
#-------------------------------------------------------------------------------

def _logger():
    """get the logger for the current Application
    
    the root logger will be used if no Application is running
    """
    if Application.initialized():
        logger = Application.instance().log
    else:
        logger = logging.getLogger()
        if not logger.handlers:
            logging.basicConfig()
    
    return logger

def _import_mapping(mapping, original=None):
    """import any string-keys in a type mapping
    
    """
    log = _logger()
    log.debug("Importing canning map")
    for key,value in mapping.items():
        if isinstance(key, basestring):
            try:
                cls = import_item(key)
            except Exception:
                if original and key not in original:
                    # only message on user-added classes
                    log.error("cannning class not importable: %r", key, exc_info=True)
                mapping.pop(key)
            else:
                mapping[cls] = mapping.pop(key)

def istype(obj, check):
    """like isinstance(obj, check), but strict
    
    This won't catch subclasses.
    """
    if isinstance(check, tuple):
        for cls in check:
            if type(obj) is cls:
                return True
        return False
    else:
        return type(obj) is check

def can(obj):
    """prepare an object for pickling"""
    
    import_needed = False
    
    for cls,canner in can_map.iteritems():
        if isinstance(cls, basestring):
            import_needed = True
            break
        elif istype(obj, cls):
            return canner(obj)
    
    if import_needed:
        # perform can_map imports, then try again
        # this will usually only happen once
        _import_mapping(can_map, _original_can_map)
        return can(obj)
    
    return obj

def can_class(obj):
    if isinstance(obj, class_type) and obj.__module__ == '__main__':
        return CannedClass(obj)
    else:
        return obj

def can_dict(obj):
    """can the *values* of a dict"""
    if istype(obj, dict):
        newobj = {}
        for k, v in obj.iteritems():
            newobj[k] = can(v)
        return newobj
    else:
        return obj

sequence_types = (list, tuple, set)

def can_sequence(obj):
    """can the elements of a sequence"""
    if istype(obj, sequence_types):
        t = type(obj)
        return t([can(i) for i in obj])
    else:
        return obj

def uncan(obj, g=None):
    """invert canning"""
    
    import_needed = False
    for cls,uncanner in uncan_map.iteritems():
        if isinstance(cls, basestring):
            import_needed = True
            break
        elif isinstance(obj, cls):
            return uncanner(obj, g)
    
    if import_needed:
        # perform uncan_map imports, then try again
        # this will usually only happen once
        _import_mapping(uncan_map, _original_uncan_map)
        return uncan(obj, g)
    
    return obj

def uncan_dict(obj, g=None):
    if istype(obj, dict):
        newobj = {}
        for k, v in obj.iteritems():
            newobj[k] = uncan(v,g)
        return newobj
    else:
        return obj

def uncan_sequence(obj, g=None):
    if istype(obj, sequence_types):
        t = type(obj)
        return t([uncan(i,g) for i in obj])
    else:
        return obj

def _uncan_dependent_hook(dep, g=None):
    dep.check_dependency()
    
def can_dependent(obj):
    return CannedObject(obj, keys=('f', 'df'), hook=_uncan_dependent_hook)

#-------------------------------------------------------------------------------
# API dictionaries
#-------------------------------------------------------------------------------

# These dicts can be extended for custom serialization of new objects

can_map = {
    'IPython.parallel.dependent' : can_dependent,
    'numpy.ndarray' : CannedArray,
    FunctionType : CannedFunction,
    bytes : CannedBytes,
    buffer : CannedBuffer,
    class_type : can_class,
}

uncan_map = {
    CannedObject : lambda obj, g: obj.get_object(g),
}

# for use in _import_mapping:
_original_can_map = can_map.copy()
_original_uncan_map = uncan_map.copy()
