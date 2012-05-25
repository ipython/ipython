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
from IPython.utils.pickleutil import can, uncan, canSequence, uncanSequence
from IPython.utils.newserialized import serialize, unserialize

if py3compat.PY3:
    buffer = memoryview

#-----------------------------------------------------------------------------
# Serialization Functions
#-----------------------------------------------------------------------------

def serialize_object(obj, threshold=64e-6):
    """Serialize an object into a list of sendable buffers.
    
    Parameters
    ----------
    
    obj : object
        The object to be serialized
    threshold : float
        The threshold for not double-pickling the content.
        
    
    Returns
    -------
    ('pmd', [bufs]) :
        where pmd is the pickled metadata wrapper,
        bufs is a list of data buffers
    """
    databuffers = []
    if isinstance(obj, (list, tuple)):
        clist = canSequence(obj)
        slist = map(serialize, clist)
        for s in slist:
            if s.typeDescriptor in ('buffer', 'ndarray') or s.getDataSize() > threshold:
                databuffers.append(s.getData())
                s.data = None
        return pickle.dumps(slist,-1), databuffers
    elif isinstance(obj, dict):
        sobj = {}
        for k in sorted(obj.iterkeys()):
            s = serialize(can(obj[k]))
            if s.typeDescriptor in ('buffer', 'ndarray') or s.getDataSize() > threshold:
                databuffers.append(s.getData())
                s.data = None
            sobj[k] = s
        return pickle.dumps(sobj,-1),databuffers
    else:
        s = serialize(can(obj))
        if s.typeDescriptor in ('buffer', 'ndarray') or s.getDataSize() > threshold:
            databuffers.append(s.getData())
            s.data = None
        return pickle.dumps(s,-1),databuffers
            
        
def unserialize_object(bufs):
    """reconstruct an object serialized by serialize_object from data buffers."""
    bufs = list(bufs)
    sobj = pickle.loads(bufs.pop(0))
    if isinstance(sobj, (list, tuple)):
        for s in sobj:
            if s.data is None:
                s.data = bufs.pop(0)
        return uncanSequence(map(unserialize, sobj)), bufs
    elif isinstance(sobj, dict):
        newobj = {}
        for k in sorted(sobj.iterkeys()):
            s = sobj[k]
            if s.data is None:
                s.data = bufs.pop(0)
            newobj[k] = uncan(unserialize(s))
        return newobj, bufs
    else:
        if sobj.data is None:
            sobj.data = bufs.pop(0)
        return uncan(unserialize(sobj)), bufs

def pack_apply_message(f, args, kwargs, threshold=64e-6):
    """pack up a function, args, and kwargs to be sent over the wire
    as a series of buffers. Any object whose data is larger than `threshold`
    will not have their data copied (currently only numpy arrays support zero-copy)"""
    msg = [pickle.dumps(can(f),-1)]
    databuffers = [] # for large objects
    sargs, bufs = serialize_object(args,threshold)
    msg.append(sargs)
    databuffers.extend(bufs)
    skwargs, bufs = serialize_object(kwargs,threshold)
    msg.append(skwargs)
    databuffers.extend(bufs)
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
    cf = pickle.loads(bufs.pop(0))
    sargs = list(pickle.loads(bufs.pop(0)))
    skwargs = dict(pickle.loads(bufs.pop(0)))
    # print sargs, skwargs
    f = uncan(cf, g)
    for sa in sargs:
        if sa.data is None:
            m = bufs.pop(0)
            if sa.getTypeDescriptor() in ('buffer', 'ndarray'):
                # always use a buffer, until memoryviews get sorted out
                sa.data = buffer(m)
                # disable memoryview support
                # if copy:
                #     sa.data = buffer(m)
                # else:
                #     sa.data = m.buffer
            else:
                if copy:
                    sa.data = m
                else:
                    sa.data = m.bytes
    
    args = uncanSequence(map(unserialize, sargs), g)
    kwargs = {}
    for k in sorted(skwargs.iterkeys()):
        sa = skwargs[k]
        if sa.data is None:
            m = bufs.pop(0)
            if sa.getTypeDescriptor() in ('buffer', 'ndarray'):
                # always use a buffer, until memoryviews get sorted out
                sa.data = buffer(m)
                # disable memoryview support
                # if copy:
                #     sa.data = buffer(m)
                # else:
                #     sa.data = m.buffer
            else:
                if copy:
                    sa.data = m
                else:
                    sa.data = m.bytes

        kwargs[k] = uncan(unserialize(sa), g)
    
    return f,args,kwargs

