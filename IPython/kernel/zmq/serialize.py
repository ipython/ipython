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

try:
    import cPickle
    pickle = cPickle
except:
    cPickle = None
    import pickle


# IPython imports
from IPython.utils import py3compat
from IPython.utils.data import flatten
from IPython.utils.pickleutil import (
    can, uncan, can_sequence, uncan_sequence, CannedObject,
    istype, sequence_types,
)

if py3compat.PY3:
    buffer = memoryview

#-----------------------------------------------------------------------------
# Serialization Functions
#-----------------------------------------------------------------------------

# default values for the thresholds:
MAX_ITEMS = 64
MAX_BYTES = 1024

def _extract_buffers(obj, threshold=MAX_BYTES):
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

def serialize_object(obj, buffer_threshold=MAX_BYTES, item_threshold=MAX_ITEMS):
    """Serialize an object into a list of sendable buffers.
    
    Parameters
    ----------
    
    obj : object
        The object to be serialized
    buffer_threshold : int
        The threshold (in bytes) for pulling out data buffers
        to avoid pickling them.
    item_threshold : int
        The maximum number of items over which canning will iterate.
        Containers (lists, dicts) larger than this will be pickled without
        introspection.
    
    Returns
    -------
    [bufs] : list of buffers representing the serialized object.
    """
    buffers = []
    if istype(obj, sequence_types) and len(obj) < item_threshold:
        cobj = can_sequence(obj)
        for c in cobj:
            buffers.extend(_extract_buffers(c, buffer_threshold))
    elif istype(obj, dict) and len(obj) < item_threshold:
        cobj = {}
        for k in sorted(obj):
            c = can(obj[k])
            buffers.extend(_extract_buffers(c, buffer_threshold))
            cobj[k] = c
    else:
        cobj = can(obj)
        buffers.extend(_extract_buffers(cobj, buffer_threshold))

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
    pobj = bufs.pop(0)
    if not isinstance(pobj, bytes):
        # a zmq message
        pobj = bytes(pobj)
    canned = pickle.loads(pobj)
    if istype(canned, sequence_types) and len(canned) < MAX_ITEMS:
        for c in canned:
            _restore_buffers(c, bufs)
        newobj = uncan_sequence(canned, g)
    elif istype(canned, dict) and len(canned) < MAX_ITEMS:
        newobj = {}
        for k in sorted(canned):
            c = canned[k]
            _restore_buffers(c, bufs)
            newobj[k] = uncan(c, g)
    else:
        _restore_buffers(canned, bufs)
        newobj = uncan(canned, g)
    
    return newobj, bufs

def pack_apply_message(f, args, kwargs, buffer_threshold=MAX_BYTES, item_threshold=MAX_ITEMS):
    """pack up a function, args, and kwargs to be sent over the wire
    
    Each element of args/kwargs will be canned for special treatment,
    but inspection will not go any deeper than that.
    
    Any object whose data is larger than `threshold`  will not have their data copied
    (only numpy arrays and bytes/buffers support zero-copy)
    
    Message will be a list of bytes/buffers of the format:
    
    [ cf, pinfo, <arg_bufs>, <kwarg_bufs> ]
    
    With length at least two + len(args) + len(kwargs)
    """
    
    arg_bufs = flatten(serialize_object(arg, buffer_threshold, item_threshold) for arg in args)
    
    kw_keys = sorted(kwargs.keys())
    kwarg_bufs = flatten(serialize_object(kwargs[key], buffer_threshold, item_threshold) for key in kw_keys)
    
    info = dict(nargs=len(args), narg_bufs=len(arg_bufs), kw_keys=kw_keys)
    
    msg = [pickle.dumps(can(f), -1),
           pickle.dumps(info, -1)]
    msg.extend(arg_bufs)
    msg.extend(kwarg_bufs)
    
    return msg

def unpack_apply_message(bufs, g=None, copy=True):
    """unpack f,args,kwargs from buffers packed by pack_apply_message()
    Returns: original f,args,kwargs"""
    bufs = list(bufs) # allow us to pop
    assert len(bufs) >= 2, "not enough buffers!"
    if not copy:
        for i in range(2):
            bufs[i] = bufs[i].bytes
    f = uncan(pickle.loads(bufs.pop(0)), g)
    info = pickle.loads(bufs.pop(0))
    arg_bufs, kwarg_bufs = bufs[:info['narg_bufs']], bufs[info['narg_bufs']:]
    
    args = []
    for i in range(info['nargs']):
        arg, arg_bufs = unserialize_object(arg_bufs, g)
        args.append(arg)
    args = tuple(args)
    assert not arg_bufs, "Shouldn't be any arg bufs left over"
    
    kwargs = {}
    for key in info['kw_keys']:
        kwarg, kwarg_bufs = unserialize_object(kwarg_bufs, g)
        kwargs[key] = kwarg
    assert not kwarg_bufs, "Shouldn't be any kwarg bufs left over"
    
    return f,args,kwargs

