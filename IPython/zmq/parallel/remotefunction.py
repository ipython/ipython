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

import map as Map
from asyncresult import AsyncMapResult

#-----------------------------------------------------------------------------
# Decorators
#-----------------------------------------------------------------------------

def remote(client, bound=False, block=None, targets=None):
    """Turn a function into a remote function.
    
    This method can be used for map:
    
    >>> @remote(client,block=True)
        def func(a)
    """
    def remote_function(f):
        return RemoteFunction(client, f, bound, block, targets)
    return remote_function

def parallel(client, dist='b', bound=False, block=None, targets='all'):
    """Turn a function into a parallel remote function.
    
    This method can be used for map:
    
    >>> @parallel(client,block=True)
        def func(a)
    """
    def parallel_function(f):
        return ParallelFunction(client, f, dist, bound, block, targets)
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
    """
    
    client = None # the remote connection
    func = None # the wrapped function
    block = None # whether to block
    bound = None # whether to affect the namespace
    targets = None # where to execute
    
    def __init__(self, client, f, bound=False, block=None, targets=None):
        self.client = client
        self.func = f
        self.block=block
        self.bound=bound
        self.targets=targets
    
    def __call__(self, *args, **kwargs):
        return self.client.apply(self.func, args=args, kwargs=kwargs,
                block=self.block, targets=self.targets, bound=self.bound)
    

class ParallelFunction(RemoteFunction):
    """Class for mapping a function to sequences."""
    def __init__(self, client, f, dist='b', bound=False, block=None, targets='all'):
        super(ParallelFunction, self).__init__(client,f,bound,block,targets)
        mapClass = Map.dists[dist]
        self.mapObject = mapClass()
    
    def __call__(self, *sequences):
        len_0 = len(sequences[0])
        for s in sequences:
            if len(s)!=len_0:
                raise ValueError('all sequences must have equal length')
        
        if self.targets is None:
            # load-balanced:
            engines = [None]*len_0
        elif isinstance(self.targets, int):
            engines = [None]*self.targets
        else:
            # multiplexed:
            engines = self.client._build_targets(self.targets)[-1]
        
        nparts = len(engines)
        msg_ids = []
        # my_f = lambda *a: map(self.func, *a)
        for index, engineid in enumerate(engines):
            args = []
            for seq in sequences:
                part = self.mapObject.getPartition(seq, index, nparts)
                if not part:
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
            mid = self.client.apply(f, args=args, block=False, 
                        bound=self.bound,
                        targets=engineid).msg_ids[0]
            msg_ids.append(mid)
        
        r = AsyncMapResult(self.client, msg_ids, self.mapObject, fname=self.func.__name__)
        if self.block:
            r.wait()
            return r.result
        else:
            return r
    
    def map(self, *sequences):
        """call a function on each element of a sequence remotely."""
        self._map = True
        ret = self.__call__(*sequences)
        del self._map
        return ret

