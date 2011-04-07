"""Remote Functions and decorators for Views."""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import warnings

from IPython.testing import decorators as testdec

from . import map as Map
from .asyncresult import AsyncMapResult

#-----------------------------------------------------------------------------
# Decorators
#-----------------------------------------------------------------------------

@testdec.skip_doctest
def remote(view, block=None, **flags):
    """Turn a function into a remote function.
    
    This method can be used for map:
    
    In [1]: @remote(view,block=True)
       ...: def func(a):
       ...:    pass
    """
    
    def remote_function(f):
        return RemoteFunction(view, f, block=block, **flags)
    return remote_function

@testdec.skip_doctest
def parallel(view, dist='b', block=None, **flags):
    """Turn a function into a parallel remote function.
    
    This method can be used for map:
    
    In [1]: @parallel(view, block=True)
       ...: def func(a):
       ...:    pass
    """
    
    def parallel_function(f):
        return ParallelFunction(view, f, dist=dist, block=block, **flags)
    return parallel_function

#--------------------------------------------------------------------------
# Classes
#--------------------------------------------------------------------------

class RemoteFunction(object):
    """Turn an existing function into a remote function.
    
    Parameters
    ----------
    
    view : View instance
        The view to be used for execution
    f : callable
        The function to be wrapped into a remote function
    block : bool [default: None]
        Whether to wait for results or not.  The default behavior is
        to use the current `block` attribute of `view`
    
    **flags : remaining kwargs are passed to View.temp_flags
    """
    
    view = None # the remote connection
    func = None # the wrapped function
    block = None # whether to block
    flags = None # dict of extra kwargs for temp_flags
    
    def __init__(self, view, f, block=None, **flags):
        self.view = view
        self.func = f
        self.block=block
        self.flags=flags
    
    def __call__(self, *args, **kwargs):
        block = self.view.block if self.block is None else self.block
        with self.view.temp_flags(block=block, **self.flags):
            return self.view.apply(self.func, *args, **kwargs)
    

class ParallelFunction(RemoteFunction):
    """Class for mapping a function to sequences.
    
    This will distribute the sequences according the a mapper, and call
    the function on each sub-sequence.  If called via map, then the function
    will be called once on each element, rather that each sub-sequence.
    
    Parameters
    ----------
    
    view : View instance
        The view to be used for execution
    f : callable
        The function to be wrapped into a remote function
    dist : str [default: 'b']
        The key for which mapObject to use to distribute sequences
        options are:
          * 'b' : use contiguous chunks in order
          * 'r' : use round-robin striping
    block : bool [default: None]
        Whether to wait for results or not.  The default behavior is
        to use the current `block` attribute of `view`
    chunksize : int or None
        The size of chunk to use when breaking up sequences in a load-balanced manner
    **flags : remaining kwargs are passed to View.temp_flags
    """
    
    chunksize=None
    mapObject=None
    
    def __init__(self, view, f, dist='b', block=None, chunksize=None, **flags):
        super(ParallelFunction, self).__init__(view, f, block=block, **flags)
        self.chunksize = chunksize
        
        mapClass = Map.dists[dist]
        self.mapObject = mapClass()
    
    def __call__(self, *sequences):
        # check that the length of sequences match
        len_0 = len(sequences[0])
        for s in sequences:
            if len(s)!=len_0:
                msg = 'all sequences must have equal length, but %i!=%i'%(len_0,len(s))
                raise ValueError(msg)
        balanced = 'Balanced' in self.view.__class__.__name__
        if balanced:
            if self.chunksize:
                nparts = len_0/self.chunksize + int(len_0%self.chunksize > 0)
            else:
                nparts = len_0
            targets = [None]*nparts
        else:
            if self.chunksize:
                warnings.warn("`chunksize` is ignored unless load balancing", UserWarning)
            # multiplexed:
            targets = self.view.targets
            nparts = len(targets)
        
        msg_ids = []
        # my_f = lambda *a: map(self.func, *a)
        client = self.view.client
        for index, t in enumerate(targets):
            args = []
            for seq in sequences:
                part = self.mapObject.getPartition(seq, index, nparts)
                if len(part) == 0:
                    continue
                else:
                    args.append(part)
            if not args:
                continue
            
            # print (args)
            if hasattr(self, '_map'):
                f = map
                args = [self.func]+args
            else:
                f=self.func
            
            view = self.view if balanced else client[t]
            with view.temp_flags(block=False, **self.flags):
                ar = view.apply(f, *args)
            
            msg_ids.append(ar.msg_ids[0])
        
        r = AsyncMapResult(self.view.client, msg_ids, self.mapObject, fname=self.func.__name__)
        
        if self.block:
            try:
                return r.get()
            except KeyboardInterrupt:
                return r
        else:
            return r
    
    def map(self, *sequences):
        """call a function on each element of a sequence remotely. 
        This should behave very much like the builtin map, but return an AsyncMapResult
        if self.block is False.
        """
        # set _map as a flag for use inside self.__call__
        self._map = True
        try:
            ret = self.__call__(*sequences)
        finally:
            del self._map
        return ret

__all__ = ['remote', 'parallel', 'RemoteFunction', 'ParallelFunction']