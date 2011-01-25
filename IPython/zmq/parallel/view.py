"""Views of remote engines"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.external.decorator import decorator
from IPython.zmq.parallel.remotefunction import ParallelFunction

#-----------------------------------------------------------------------------
# Decorators
#-----------------------------------------------------------------------------

@decorator
def myblock(f, self, *args, **kwargs):
    """override client.block with self.block during a call"""
    block = self.client.block
    self.client.block = self.block
    ret = f(self, *args, **kwargs)
    self.client.block = block
    return ret

@decorator
def save_ids(f, self, *args, **kwargs):
    """Keep our history and outstanding attributes up to date after a method call."""
    n_previous = len(self.client.history)
    ret = f(self, *args, **kwargs)
    nmsgs = len(self.client.history) - n_previous
    msg_ids = self.client.history[-nmsgs:]
    self.history.extend(msg_ids)
    map(self.outstanding.add, msg_ids)
    return ret

@decorator
def sync_results(f, self, *args, **kwargs):
    """sync relevant results from self.client to our results attribute."""
    ret = f(self, *args, **kwargs)
    delta = self.outstanding.difference(self.client.outstanding)
    completed = self.outstanding.intersection(delta)
    self.outstanding = self.outstanding.difference(completed)
    for msg_id in completed:
        self.results[msg_id] = self.client.results[msg_id]
    return ret

@decorator
def spin_after(f, self, *args, **kwargs):
    """call spin after the method."""
    ret = f(self, *args, **kwargs)
    self.spin()
    return ret

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class View(object):
    """Base View class for more convenint apply(f,*args,**kwargs) syntax via attributes.
    
    Don't use this class, use subclasses.
    """
    _targets = None
    _ntargets = None
    block=None
    bound=None
    history=None
    
    def __init__(self, client, targets=None):
        self.client = client
        self._targets = targets
        self._ntargets = 1 if isinstance(targets, (int,type(None))) else len(targets)
        self.block = client.block
        self.bound=True
        self.history = []
        self.outstanding = set()
        self.results = {}

    def __repr__(self):
        strtargets = str(self._targets)
        if len(strtargets) > 16:
            strtargets = strtargets[:12]+'...]'
        return "<%s %s>"%(self.__class__.__name__, strtargets)

    @property
    def targets(self):
        return self._targets

    @targets.setter
    def targets(self, value):
        raise AttributeError("Cannot set my targets argument after construction!")

    @sync_results
    def spin(self):
        """spin the client, and sync"""
        self.client.spin()

    @sync_results
    @save_ids
    def apply(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) on remote engines, returning the result.
        
        This method does not involve the engine's namespace.
        
        if self.block is False:
            returns msg_id
        else:
            returns actual result of f(*args, **kwargs)
        """
        return self.client.apply(f, args, kwargs, block=self.block, targets=self.targets, bound=self.bound)

    @save_ids
    def apply_async(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) on remote engines in a nonblocking manner.
        
        This method does not involve the engine's namespace.
        
        returns msg_id
        """
        return self.client.apply(f,args,kwargs, block=False, targets=self.targets, bound=False)

    @spin_after
    @save_ids
    def apply_sync(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) on remote engines in a blocking manner,
         returning the result.
        
        This method does not involve the engine's namespace.
        
        returns: actual result of f(*args, **kwargs)
        """
        return self.client.apply(f,args,kwargs, block=True, targets=self.targets, bound=False)

    @sync_results
    @save_ids
    def apply_bound(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) bound to engine namespace(s).
        
        if self.block is False:
            returns msg_id
        else:
            returns actual result of f(*args, **kwargs)
        
        This method has access to the targets' globals
        
        """
        return self.client.apply(f, args, kwargs, block=self.block, targets=self.targets, bound=True)

    @sync_results
    @save_ids
    def apply_async_bound(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) bound to engine namespace(s) 
        in a nonblocking manner.
        
        returns: msg_id
        
        This method has access to the targets' globals
        
        """
        return self.client.apply(f, args, kwargs, block=False, targets=self.targets, bound=True)

    @spin_after
    @save_ids
    def apply_sync_bound(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) bound to engine namespace(s), waiting for the result.
        
        returns: actual result of f(*args, **kwargs)
        
        This method has access to the targets' globals
        
        """
        return self.client.apply(f, args, kwargs, block=True, targets=self.targets, bound=True)
    
    @spin_after
    @save_ids
    def map(self, f, *sequences):
        """Parallel version of builtin `map`, using this view's engines."""
        if isinstance(self.targets, int):
            targets = [self.targets]
        pf = ParallelFunction(self.client, f, block=self.block,
                        bound=True, targets=targets)
        return pf.map(*sequences)
    
    def abort(self, msg_ids=None, block=None):
        """Abort jobs on my engines.
        
        Parameters
        ----------
        
        msg_ids : None, str, list of strs, optional
            if None: abort all jobs.
            else: abort specific msg_id(s).
        """
        block = block if block is not None else self.block
        return self.client.abort(msg_ids=msg_ids, targets=self.targets, block=block)

    def queue_status(self, verbose=False):
        """Fetch the Queue status of my engines"""
        return self.client.queue_status(targets=self.targets, verbose=verbose)
    
    def purge_results(self, msg_ids=[],targets=[]):
        """Instruct the controller to forget specific results."""
        if targets is None or targets == 'all':
            targets = self.targets
        return self.client.purge_results(msg_ids=msg_ids, targets=targets)


class DirectView(View):
    """Direct Multiplexer View of one or more engines.
    
    These are created via indexed access to a client:
    
    >>> dv_1 = client[1]
    >>> dv_all = client[:]
    >>> dv_even = client[::2]
    >>> dv_some = client[1:3]
    
    """
    
    def update(self, ns):
        """update remote namespace with dict `ns`"""
        return self.client.push(ns, targets=self.targets, block=self.block)
    
    push = update
    
    def get(self, key_s):
        """get object(s) by `key_s` from remote namespace
        will return one object if it is a key.
        It also takes a list of keys, and will return a list of objects."""
        # block = block if block is not None else self.block
        return self.client.pull(key_s, block=True, targets=self.targets)
    
    def pull(self, key_s, block=True):
        """get object(s) by `key_s` from remote namespace
        will return one object if it is a key.
        It also takes a list of keys, and will return a list of objects."""
        block = block if block is not None else self.block
        return self.client.pull(key_s, block=block, targets=self.targets)
    
    def scatter(self, key, seq, dist='b', flatten=False, targets=None, block=None):
        """
        Partition a Python sequence and send the partitions to a set of engines.
        """
        block = block if block is not None else self.block
        if targets is None:
            targets = self.targets
        
        return self.client.scatter(key, seq, dist=dist, flatten=flatten,
                    targets=targets, block=block)
    
    def gather(self, key, dist='b', targets=None, block=True):
        """
        Gather a partitioned sequence on a set of engines as a single local seq.
        """
        block = block if block is not None else self.block
        if targets is None:
            targets = self.targets
        
        return self.client.gather(key, dist=dist, targets=targets, block=block)
    
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self,key, value):
        self.update({key:value})
    
    def clear(self, block=False):
        """Clear the remote namespaces on my engines."""
        block = block if block is not None else self.block
        return self.client.clear(targets=self.targets, block=block)
    
    def kill(self, block=True):
        """Kill my engines."""
        block = block if block is not None else self.block
        return self.client.kill(targets=self.targets, block=block)
    
class LoadBalancedView(View):
    """An engine-agnostic View that only executes via the Task queue.
    
    Typically created via:
    
    >>> lbv = client[None]
    <LoadBalancedView tcp://127.0.0.1:12345>
    
    but can also be created with:
    
    >>> lbc = LoadBalancedView(client)
    
    TODO: allow subset of engines across which to balance.
    """
    def __repr__(self):
        return "<%s %s>"%(self.__class__.__name__, self.client._addr)
    
    