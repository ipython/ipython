"""AsyncResult objects for the client"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import error

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class AsyncResult(object):
    """Class for representing results of non-blocking calls.
    
    Provides the same interface as :py:class:`multiprocessing.AsyncResult`.
    """
    def __init__(self, client, msg_ids, targets=None):
        self._client = client
        self.msg_ids = msg_ids
        self._targets=targets
        self._ready = False
        self._success = None
    
    def __repr__(self):
        if self._ready:
            return "<%s: finished>"%(self.__class__.__name__)
        else:
            return "<%s: %r>"%(self.__class__.__name__,self.msg_ids)
    
    
    def _reconstruct_result(self, res):
        """
        Override me in subclasses for turning a list of results
        into the expected form.
        """
        if len(res) == 1:
            return res[0]
        elif self.targets is not None:
            return dict(zip(self._targets, res))
        else:
            return res
        
    def get(self, timeout=-1):
        """Return the result when it arrives. 
        
        If `timeout` is not ``None`` and the result does not arrive within
        `timeout` seconds then ``TimeoutError`` is raised. If the
        remote call raised an exception then that exception will be reraised
        by get().
        """
        if not self.ready():
            self.wait(timeout)
        
        if self._ready:
            if self._success:
                return self._result
            else:
                raise self._exception
        else:
            raise error.TimeoutError("Result not ready.")
    
    def ready(self):
        """Return whether the call has completed."""
        if not self._ready:
            self.wait(0)
        return self._ready
    
    def wait(self, timeout=-1):
        """Wait until the result is available or until `timeout` seconds pass.
        """
        if self._ready:
            return
        self._ready = self._client.barrier(self.msg_ids, timeout)
        if self._ready:
            try:
                results = map(self._client.results.get, self.msg_ids)
                results = error.collect_exceptions(results, 'get')
                self._result = self._reconstruct_result(results)
            except Exception, e:
                self._exception = e
                self._success = False
            else:
                self._success = True
            
    
    def successful(self):
        """Return whether the call completed without raising an exception. 
        
        Will raise ``AssertionError`` if the result is not ready.
        """
        assert self._ready
        return self._success

class AsyncMapResult(AsyncResult):
    """Class for representing results of non-blocking gathers.
    
    This will properly reconstruct the gather.
    """
    
    def __init__(self, client, msg_ids, mapObject):
        self._mapObject = mapObject
        AsyncResult.__init__(self, client, msg_ids)
    
    def _reconstruct_result(self, res):
        """Perform the gather on the actual results."""
        return self._mapObject.joinPartitions(res)
    
        
