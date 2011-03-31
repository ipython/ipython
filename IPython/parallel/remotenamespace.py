"""RemoteNamespace object, for dict style interaction with a remote
execution kernel."""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from functools import wraps
from IPython.external.decorator import decorator

def _clear():
    globals().clear()

@decorator
def spinfirst(f):
    @wraps(f)
    def spun_method(self, *args, **kwargs):
        self.spin()
        return f(self, *args, **kwargs)
    return spun_method

@decorator
def myblock(f, self, *args, **kwargs):
    block = self.client.block
    self.client.block = self.block
    ret = f(self, *args, **kwargs)
    self.client.block = block
    return ret

class RemoteNamespace(object):
    """A RemoteNamespace object, providing dictionary 
    access to an engine via an IPython.zmq.client object.
    
    
    """
    client = None
    queue = None
    id = None
    block = False
    
    def __init__(self, client, id):
        self.client = client
        self.id = id
        self.block = client.block # initial state is same as client
    
    def __repr__(self):
        return "<RemoteNamespace[%i]>"%self.id
    
    @myblock
    def apply(self, f, *args, **kwargs):
        """call f(*args, **kwargs) in remote namespace
        
        This method has no access to the user namespace"""
        return self.client.apply_to(self.id, f, *args, **kwargs)
    
    @myblock
    def apply_bound(self, f, *args, **kwargs):
        """call `f(*args, **kwargs)` in remote namespace.
        
        `f` will have access to the user namespace as globals()."""
        return self.client.apply_bound_to(self.id, f, *args, **kwargs)
    
    @myblock
    def update(self, ns):
        """update remote namespace with dict `ns`"""
        return self.client.push(self.id, ns, self.block)
    
    def get(self, key_s):
        """get object(s) by `key_s` from remote namespace
        will return one object if it is a key.
        It also takes a list of keys, and will return a list of objects."""
        return self.client.pull(self.id, key_s, self.block)
    
    push = update
    pull = get
    
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self,key,value):
        self.update({key:value})
    
    def clear(self):
        """clear the remote namespace"""
        return self.client.apply_bound_to(self.id, _clear)
    
    @decorator
    def withme(self, toapply):
        """for use as a decorator, this turns a function into
        one that executes remotely."""
        @wraps(toapply)
        def applied(self, *args, **kwargs):
            return self.apply_bound(self, toapply, *args, **kwargs)
        return applied
        
        



