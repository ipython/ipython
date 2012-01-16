"""Remote Functions and decorators for Views.

Authors:

* Brian Granger
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

from __future__ import division

import sys
import warnings

from IPython.testing.skipdoctest import skip_doctest

from . import map as Map
from .asyncresult import AsyncMapResult

#-----------------------------------------------------------------------------
# Functions and Decorators
#-----------------------------------------------------------------------------

@skip_doctest
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

@skip_doctest
def parallel(view, dist='b', block=None, ordered=True, **flags):
    """Turn a function into a parallel remote function.

    This method can be used for map:

    In [1]: @parallel(view, block=True)
       ...: def func(a):
       ...:    pass
    """

    def parallel_function(f):
        return ParallelFunction(view, f, dist=dist, block=block, ordered=ordered, **flags)
    return parallel_function

def getname(f):
    """Get the name of an object.
    
    For use in case of callables that are not functions, and
    thus may not have __name__ defined.
    
    Order: f.__name__ >  f.name > str(f)
    """
    try:
        return f.__name__
    except:
        pass
    try:
        return f.name
    except:
        pass
    
    return str(f)

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
    ordered : bool [default: True]
        Whether 
    **flags : remaining kwargs are passed to View.temp_flags
    """

    chunksize=None
    ordered=None
    mapObject=None

    def __init__(self, view, f, dist='b', block=None, chunksize=None, ordered=True, **flags):
        super(ParallelFunction, self).__init__(view, f, block=block, **flags)
        self.chunksize = chunksize
        self.ordered = ordered

        mapClass = Map.dists[dist]
        self.mapObject = mapClass()

    def __call__(self, *sequences):
        client = self.view.client
        
        # check that the length of sequences match
        len_0 = len(sequences[0])
        for s in sequences:
            if len(s)!=len_0:
                msg = 'all sequences must have equal length, but %i!=%i'%(len_0,len(s))
                raise ValueError(msg)
        balanced = 'Balanced' in self.view.__class__.__name__
        if balanced:
            if self.chunksize:
                nparts = len_0//self.chunksize + int(len_0%self.chunksize > 0)
            else:
                nparts = len_0
            targets = [None]*nparts
        else:
            if self.chunksize:
                warnings.warn("`chunksize` is ignored unless load balancing", UserWarning)
            # multiplexed:
            targets = self.view.targets
            # 'all' is lazily evaluated at execution time, which is now:
            if targets == 'all':
                targets = client._build_targets(targets)[1]
            nparts = len(targets)

        msg_ids = []
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
                if sys.version_info[0] >= 3:
                    f = lambda f, *sequences: list(map(f, *sequences))
                else:
                    f = map
                args = [self.func]+args
            else:
                f=self.func

            view = self.view if balanced else client[t]
            with view.temp_flags(block=False, **self.flags):
                ar = view.apply(f, *args)

            msg_ids.append(ar.msg_ids[0])

        r = AsyncMapResult(self.view.client, msg_ids, self.mapObject, 
                            fname=getname(self.func),
                            ordered=self.ordered
                        )

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
