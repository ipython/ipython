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

from IPython.external.decorator import decorator
import error

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

@decorator
def check_ready(f, self, *args, **kwargs):
    """Call spin() to sync state prior to calling the method."""
    self.wait(0)
    if not self._ready:
        raise error.TimeoutError("result not ready")
    return f(self, *args, **kwargs)

class AsyncResult(object):
    """Class for representing results of non-blocking calls.
    
    Provides the same interface as :py:class:`multiprocessing.AsyncResult`.
    """
    
    msg_ids = None
    
    def __init__(self, client, msg_ids, fname=''):
        self._client = client
        self.msg_ids = msg_ids
        self._fname=fname
        self._ready = False
        self._success = None
        self._single_result = len(msg_ids) == 1
    
    def __repr__(self):
        if self._ready:
            return "<%s: finished>"%(self.__class__.__name__)
        else:
            return "<%s: %s>"%(self.__class__.__name__,self._fname)
    
    
    def _reconstruct_result(self, res):
        """
        Override me in subclasses for turning a list of results
        into the expected form.
        """
        if self._single_result:
            return res[0]
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
                self._result = results
                if self._single_result:
                    r = results[0]
                    if isinstance(r, Exception):
                        raise r
                else:
                    results = error.collect_exceptions(results, self._fname)
                self._result = self._reconstruct_result(results)
            except Exception, e:
                self._exception = e
                self._success = False
            else:
                self._success = True
            finally:
                self._metadata = map(self._client.metadata.get, self.msg_ids)
            
    
    def successful(self):
        """Return whether the call completed without raising an exception. 
        
        Will raise ``AssertionError`` if the result is not ready.
        """
        assert self._ready
        return self._success
    
    #----------------------------------------------------------------
    # Extra methods not in mp.pool.AsyncResult
    #----------------------------------------------------------------
    
    def get_dict(self, timeout=-1):
        """Get the results as a dict, keyed by engine_id."""
        results = self.get(timeout)
        engine_ids = [ md['engine_id'] for md in self._metadata ]
        bycount = sorted(engine_ids, key=lambda k: engine_ids.count(k))
        maxcount = bycount.count(bycount[-1])
        if maxcount > 1:
            raise ValueError("Cannot build dict, %i jobs ran on engine #%i"%(
                    maxcount, bycount[-1]))
        
        return dict(zip(engine_ids,results))
    
    @property
    @check_ready
    def result(self):
        """result property."""
        return self._result
    
    # abbreviated alias:
    r = result
    
    @property
    @check_ready
    def metadata(self):
        """metadata property."""
        if self._single_result:
            return self._metadata[0]
        else:
            return self._metadata
    
    @property
    def result_dict(self):
        """result property as a dict."""
        return self.get_dict(0)
    
    def __dict__(self):
        return self.get_dict(0)

    #-------------------------------------
    # dict-access
    #-------------------------------------
    
    @check_ready
    def __getitem__(self, key):
        """getitem returns result value(s) if keyed by int/slice, or metadata if key is str.
        """
        if isinstance(key, int):
            return error.collect_exceptions([self._result[key]], self._fname)[0]
        elif isinstance(key, slice):
            return error.collect_exceptions(self._result[key], self._fname)
        elif isinstance(key, basestring):
            values = [ md[key] for md in self._metadata ]
            if self._single_result:
                return values[0]
            else:
                return values
        else:
            raise TypeError("Invalid key type %r, must be 'int','slice', or 'str'"%type(key))
    
    @check_ready
    def __getattr__(self, key):
        """getattr maps to getitem for convenient access to metadata."""
        if key not in self._metadata[0].keys():
            raise AttributeError("%r object has no attribute %r"%(
                    self.__class__.__name__, key))
        return self.__getitem__(key)

    
class AsyncMapResult(AsyncResult):
    """Class for representing results of non-blocking gathers.
    
    This will properly reconstruct the gather.
    """
    
    def __init__(self, client, msg_ids, mapObject, fname=''):
        AsyncResult.__init__(self, client, msg_ids, fname=fname)
        self._mapObject = mapObject
        self._single_result = False
    
    def _reconstruct_result(self, res):
        """Perform the gather on the actual results."""
        return self._mapObject.joinPartitions(res)
    
        
__all__ = ['AsyncResult', 'AsyncMapResult']