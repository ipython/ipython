"""Remote Functions and decorators for the client."""
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

import map as Map
from asyncresult import AsyncMapResult

#-----------------------------------------------------------------------------
# Decorators
#-----------------------------------------------------------------------------

@testdec.skip_doctest
def remote(client, bound=True, block=None, targets=None, balanced=None):
    """Turn a function into a remote function.
    
    This method can be used for map:
    
    In [1]: @remote(client,block=True)
       ...: def func(a):
       ...:    pass
    """
    
    def remote_function(f):
        return RemoteFunction(client, f, bound, block, targets, balanced)
    return remote_function

@testdec.skip_doctest
def parallel(client, dist='b', bound=True, block=None, targets='all', balanced=None):
    """Turn a function into a parallel remote function.
    
    This method can be used for map:
    
    In [1]: @parallel(client,block=True)
       ...: def func(a):
       ...:    pass
    """
    
    def parallel_function(f):
        return ParallelFunction(client, f, dist, bound, block, targets, balanced)
    return parallel_function

#--------------------------------------------------------------------------
# Classes
#--------------------------------------------------------------------------

class RemoteFunction(object):
    """Turn an existing function into a remote function.
    
    Parameters
    ----------
    
    client : Client instance
        The client to be used to connect to engines
    f : callable
        The function to be wrapped into a remote function
    bound : bool [default: False]
        Whether the affect the remote namespace when called
    block : bool [default: None]
        Whether to wait for results or not.  The default behavior is
        to use the current `block` attribute of `client`
    targets : valid target list [default: all]
        The targets on which to execute.
    balanced : bool
        Whether to load-balance with the Task scheduler or not
    """
    
    client = None # the remote connection
    func = None # the wrapped function
    block = None # whether to block
    bound = None # whether to affect the namespace
    targets = None # where to execute
    balanced = None # whether to load-balance
    
    def __init__(self, client, f, bound=False, block=None, targets=None, balanced=None):
        self.client = client
        self.func = f
        self.block=block
        self.bound=bound
        self.targets=targets
        if balanced is None:
            if targets is None:
                balanced = True
            else:
                balanced = False
        self.balanced = balanced
    
    def __call__(self, *args, **kwargs):
        return self.client.apply(self.func, args=args, kwargs=kwargs,
                block=self.block, targets=self.targets, bound=self.bound, balanced=self.balanced)
    

class ParallelFunction(RemoteFunction):
    """Class for mapping a function to sequences."""
    def __init__(self, client, f, dist='b', bound=False, block=None, targets='all', balanced=None, chunk_size=None):
        super(ParallelFunction, self).__init__(client,f,bound,block,targets,balanced)
        self.chunk_size = chunk_size
        
        mapClass = Map.dists[dist]
        self.mapObject = mapClass()
    
    def __call__(self, *sequences):
        len_0 = len(sequences[0])
        for s in sequences:
            if len(s)!=len_0:
                msg = 'all sequences must have equal length, but %i!=%i'%(len_0,len(s))
                raise ValueError(msg)
        
        if self.balanced:
            if self.chunk_size:
                nparts = len_0/self.chunk_size + int(len_0%self.chunk_size > 0)
            else:
                nparts = len_0
            targets = [self.targets]*nparts
        else:
            if self.chunk_size:
                warnings.warn("`chunk_size` is ignored when `balanced=False", UserWarning)
            # multiplexed:
            targets = self.client._build_targets(self.targets)[-1]
            nparts = len(targets)
        
        msg_ids = []
        # my_f = lambda *a: map(self.func, *a)
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
            ar = self.client.apply(f, args=args, block=False, bound=self.bound, 
                        targets=t, balanced=self.balanced)
            
            msg_ids.append(ar.msg_ids[0])
        
        r = AsyncMapResult(self.client, msg_ids, self.mapObject, fname=self.func.__name__)
        if self.block:
            try:
                return r.get()
            except KeyboardInterrupt:
                return r
        else:
            return r
    
    def map(self, *sequences):
        """call a function on each element of a sequence remotely."""
        self._map = True
        try:
            ret = self.__call__(*sequences)
        finally:
            del self._map
        return ret

