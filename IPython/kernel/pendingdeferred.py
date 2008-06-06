# encoding: utf-8
# -*- test-case-name: IPython.kernel.test.test_pendingdeferred -*-

"""Classes to manage pending Deferreds.

A pending deferred is a deferred that may or may not have fired.  This module
is useful for taking a class whose methods return deferreds and wrapping it to
provide API that keeps track of those deferreds for later retrieval.  See the
tests for examples of its usage.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import log, components, failure
from zope.interface import Interface, implements, Attribute

from IPython.kernel.twistedutil import gatherBoth
from IPython.kernel import error
from IPython.external import guid
from IPython.tools import growl

class PendingDeferredManager(object):
    """A class to track pending deferreds.
    
    To track a pending deferred, the user of this class must first
    get a deferredID by calling `get_next_deferred_id`.  Then the user
    calls `save_pending_deferred` passing that id and the deferred to
    be tracked.  To later retrieve it, the user calls
    `get_pending_deferred` passing the id.
    """
    
    def __init__(self):
        """Manage pending deferreds."""

        self.results = {} # Populated when results are ready
        self.deferred_ids = [] # List of deferred ids I am managing
        self.deferreds_to_callback = {} # dict of lists of deferreds to callback
        
    def get_deferred_id(self):
        return guid.generate()
    
    def quick_has_id(self, deferred_id):
        return deferred_id in self.deferred_ids
    
    def _save_result(self, result, deferred_id):
        if self.quick_has_id(deferred_id):
            self.results[deferred_id] = result
            self._trigger_callbacks(deferred_id)
    
    def _trigger_callbacks(self, deferred_id):
        # Go through and call the waiting callbacks
        result = self.results.get(deferred_id)
        if result is not None:  # Only trigger if there is a result
            try:
                d = self.deferreds_to_callback.pop(deferred_id)
            except KeyError:
                d = None
            if d is not None:
                if isinstance(result, failure.Failure):
                    d.errback(result)
                else:
                    d.callback(result)
                self.delete_pending_deferred(deferred_id)
                   
    def save_pending_deferred(self, d, deferred_id=None):
        """Save the result of a deferred for later retrieval.
        
        This works even if the deferred has not fired.
        
        Only callbacks and errbacks applied to d before this method
        is called will be called no the final result.
        """
        if deferred_id is None:
            deferred_id = self.get_deferred_id()
        self.deferred_ids.append(deferred_id)
        d.addBoth(self._save_result, deferred_id)
        return deferred_id
    
    def _protected_del(self, key, container):
        try:
            del container[key]
        except Exception:
            pass
    
    def delete_pending_deferred(self, deferred_id):
        """Remove a deferred I am tracking and add a null Errback.
        
        :Parameters:
            deferredID : str
                The id of a deferred that I am tracking.
        """
        if self.quick_has_id(deferred_id):
            # First go through a errback any deferreds that are still waiting
            d = self.deferreds_to_callback.get(deferred_id)
            if d is not None:
                d.errback(failure.Failure(error.AbortedPendingDeferredError("pending deferred has been deleted: %r"%deferred_id)))
            # Now delete all references to this deferred_id
            ind = self.deferred_ids.index(deferred_id)
            self._protected_del(ind, self.deferred_ids)
            self._protected_del(deferred_id, self.deferreds_to_callback)
            self._protected_del(deferred_id, self.results)            
        else:
            raise error.InvalidDeferredID('invalid deferred_id: %r' % deferred_id)
    
    def clear_pending_deferreds(self):
        """Remove all the deferreds I am tracking."""
        for did in self.deferred_ids:
            self.delete_pending_deferred(did)
        
    def _delete_and_pass_through(self, r, deferred_id):
        self.delete_pending_deferred(deferred_id)
        return r
        
    def get_pending_deferred(self, deferred_id, block):
        if not self.quick_has_id(deferred_id) or self.deferreds_to_callback.get(deferred_id) is not None:
            return defer.fail(failure.Failure(error.InvalidDeferredID('invalid deferred_id: %r' + deferred_id)))
        result = self.results.get(deferred_id)
        if result is not None:
            self.delete_pending_deferred(deferred_id)
            if isinstance(result, failure.Failure):
                return defer.fail(result)
            else:
                return defer.succeed(result)
        else:  # Result is not ready
            if block:
                d = defer.Deferred()
                self.deferreds_to_callback[deferred_id] = d
                return d
            else:
                return defer.fail(failure.Failure(error.ResultNotCompleted("result not completed: %r" % deferred_id)))

def two_phase(wrapped_method):
    """Wrap methods that return a deferred into a two phase process.
    
    This transforms::
    
        foo(arg1, arg2, ...) -> foo(arg1, arg2,...,block=True).
    
    The wrapped method will then return a deferred to a deferred id.  This will
    only work on method of classes that inherit from `PendingDeferredManager`,
    as that class provides an API for 
    
    block is a boolean to determine if we should use the two phase process or
    just simply call the wrapped method.  At this point block does not have a
    default and it probably won't.
    """
    
    def wrapper_two_phase(pdm, *args, **kwargs):
        try:
            block = kwargs.pop('block')
        except KeyError:
            block = True  # The default if not specified
        if block:
            return wrapped_method(pdm, *args, **kwargs)
        else:
            d = wrapped_method(pdm, *args, **kwargs)
            deferred_id=pdm.save_pending_deferred(d)
            return defer.succeed(deferred_id)
    
    return wrapper_two_phase
                
                
            
            
                
