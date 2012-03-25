"""serialization utilities for apply messages

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
import logging
import os
import re
import socket
import sys

try:
    import cPickle
    pickle = cPickle
except:
    cPickle = None
    import pickle


# IPython imports
from IPython.utils import py3compat
from IPython.utils.pickleutil import (
    can, uncan, can_sequence, uncan_sequence, CannedObject
) 
from IPython.utils.newserialized import serialize, unserialize

if py3compat.PY3:
    buffer = memoryview

#-----------------------------------------------------------------------------
# Serialization Functions
#-----------------------------------------------------------------------------

# maximum items to iterate through in a container
MAX_ITEMS = 64

def _extract_buffers(obj, threshold=1024):
    """extract buffers larger than a certain threshold"""
    buffers = []
    if isinstance(obj, CannedObject) and obj.buffers:
        for i,buf in enumerate(obj.buffers):
            if len(buf) > threshold:
                # buffer larger than threshold, prevent pickling
                obj.buffers[i] = None
                buffers.append(buf)
            elif isinstance(buf, buffer):
                # buffer too small for separate send, coerce to bytes
                # because pickling buffer objects just results in broken pointers
                obj.buffers[i] = bytes(buf)
    return buffers

def _restore_buffers(obj, buffers):
    """restore buffers extracted by """
    if isinstance(obj, CannedObject) and obj.buffers:
        for i,buf in enumerate(obj.buffers):
            if buf is None:
                obj.buffers[i] = buffers.pop(0)

def serialize_object(obj, threshold=1024):
    """Serialize an object into a list of sendable buffers.
    
    Parameters
    ----------
    
    obj : object
        The object to be serialized
    threshold : int
        The threshold (in bytes) for pulling out data buffers
        to avoid pickling them.
    
    Returns
    -------
    [bufs] : list of buffers representing the serialized object.
    """
    buffers = []
    if isinstance(obj, (list, tuple)) and len(obj) < MAX_ITEMS:
        cobj = can_sequence(obj)
        for c in cobj:
            buffers.extend(_extract_buffers(c, threshold))
    elif isinstance(obj, dict) and len(obj) < MAX_ITEMS:
        cobj = {}
        for k in sorted(obj.iterkeys()):
            c = can(obj[k])
            buffers.extend(_extract_buffers(c, threshold))
            cobj[k] = c
    else:
        cobj = can(obj)
        buffers.extend(_extract_buffers(cobj, threshold))

    buffers.insert(0, pickle.dumps(cobj,-1))
    return buffers

def unserialize_object(buffers, g=None):
    """reconstruct an object serialized by serialize_object from data buffers.
    
    Parameters
    ----------
    
    bufs : list of buffers/bytes
    
    g : globals to be used when uncanning
    
    Returns
    -------
    
    (newobj, bufs) : unpacked object, and the list of remaining unused buffers.
    """
    bufs = list(buffers)
    canned = pickle.loads(bufs.pop(0))
    if isinstance(canned, (list, tuple)) and len(canned) < MAX_ITEMS:
        for c in canned:
            _restore_buffers(c, bufs)
        newobj = uncan_sequence(canned, g)
    elif isinstance(canned, dict) and len(canned) < MAX_ITEMS:
        newobj = {}
        for k in sorted(canned.iterkeys()):
            c = canned[k]
            _restore_buffers(c, bufs)
            newobj[k] = uncan(c, g)
    else:
        _restore_buffers(canned, bufs)
        newobj = uncan(canned, g)
    
    return newobj, bufs

def pack_apply_message(f, args, kwargs, threshold=1024):
    """pack up a function, args, and kwargs to be sent over the wire
    as a series of buffers. Any object whose data is larger than `threshold`
    will not have their data copied (currently only numpy arrays support zero-copy)
    """
    msg = [pickle.dumps(can(f),-1)]
    databuffers = [] # for large objects
    sargs = serialize_object(args,threshold)
    msg.append(sargs[0])
    databuffers.extend(sargs[1:])
    skwargs = serialize_object(kwargs,threshold)
    msg.append(skwargs[0])
    databuffers.extend(skwargs[1:])
    msg.extend(databuffers)
    return msg

def unpack_apply_message(bufs, g=None, copy=True):
    """unpack f,args,kwargs from buffers packed by pack_apply_message()
    Returns: original f,args,kwargs"""
    bufs = list(bufs) # allow us to pop
    assert len(bufs) >= 3, "not enough buffers!"
    if not copy:
        for i in range(3):
            bufs[i] = bufs[i].bytes
    f = uncan(pickle.loads(bufs.pop(0)), g)
    # sargs = bufs.pop(0)
    # pop kwargs out, so first n-elements are args, serialized
    skwargs = bufs.pop(1)
    args, bufs = unserialize_object(bufs, g)
    # put skwargs back in as the first element
    bufs.insert(0, skwargs)
    kwargs, bufs = unserialize_object(bufs, g)
    
    assert not bufs, "Shouldn't be any data left over"
    
    return f,args,kwargs

