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

from IPython.external.decorator import decorator
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

@decorator
def sync_view_results(f, self, *args, **kwargs):
    """sync relevant results from self.client to our results attribute.
    
    This is a clone of view.sync_results, but for remote functions
    """
    view = self.view
    if view._in_sync_results:
        return f(self, *args, **kwargs)
    print 'in sync results', f
    view._in_sync_results = True
    try:
        ret = f(self, *args, **kwargs)
    finally:
        view._in_sync_results = False
        view._sync_results()
    return ret
    
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
        Whether the result should be kept in order. If False,
        results become available as they arrive, regardless of submission order.
    **flags : remaining kwargs are passed to View.temp_flags
    """

    chunksize = None
    ordered = None
    mapObject = None
    _mapping = False

    def __init__(self, view, f, dist='b', block=None, chunksize=None, ordered=True, **flags):
        super(ParallelFunction, self).__init__(view, f, block=block, **flags)
        self.chunksize = chunksize
        self.ordered = ordered

        mapClass = Map.dists[dist]
        self.mapObject = mapClass()
    
    @sync_view_results
    def __call__(self, *sequences):
        client = self.view.client
        
        lens = []
        maxlen = minlen = -1
        for i, seq in enumerate(sequences):
            try:
                n = len(seq)
            except Exception:
                seq = list(seq)
                if isinstance(sequences, tuple):
                    # can't alter a tuple
                    sequences = list(sequences)
                sequences[i] = seq
                n = len(seq)
            if n > maxlen:
                maxlen = n
            if minlen == -1 or n < minlen:
                minlen = n
            lens.append(n)
        
        # check that the length of sequences match
        if not self._mapping and minlen != maxlen:
            msg = 'all sequences must have equal length, but have %s' % lens
            raise ValueError(msg)
        
        balanced = 'Balanced' in self.view.__class__.__name__
        if balanced:
            if self.chunksize:
                nparts = maxlen // self.chunksize + int(maxlen % self.chunksize > 0)
            else:
                nparts = maxlen
            targets = [None]*nparts
        else:
            if self.chunksize:
                warnings.warn("`chunksize` is ignored unless load balancing", UserWarning)
            # multiplexed:
            targets = self.view.targets
            # 'all' is lazily evaluated at execution time, which is now:
            if targets == 'all':
                targets = client._build_targets(targets)[1]
            elif isinstance(targets, int):
                # single-engine view, targets must be iterable
                targets = [targets]
            nparts = len(targets)

        msg_ids = []
        for index, t in enumerate(targets):
            args = []
            for seq in sequences:
                part = self.mapObject.getPartition(seq, index, nparts, maxlen)
                args.append(part)
            if not any(args):
                continue

            if self._mapping:
                if sys.version_info[0] >= 3:
                    f = lambda f, *sequences: list(map(f, *sequences))
                else:
                    f = map
                args = [self.func] + args
            else:
                f=self.func

            view = self.view if balanced else client[t]
            with view.temp_flags(block=False, **self.flags):
                ar = view.apply(f, *args)

            msg_ids.extend(ar.msg_ids)

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
        # set _mapping as a flag for use inside self.__call__
        self._mapping = True
        try:
            ret = self(*sequences)
        finally:
            self._mapping = False
        return ret

__all__ = ['remote', 'parallel', 'RemoteFunction', 'ParallelFunction']
