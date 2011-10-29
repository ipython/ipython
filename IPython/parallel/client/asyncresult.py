"""AsyncResult objects for the client

Authors:

* MinRK
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

import time

from zmq import MessageTracker

from IPython.external.decorator import decorator
from IPython.parallel import error

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

# global empty tracker that's always done:
finished_tracker = MessageTracker()

@decorator
def check_ready(f, self, *args, **kwargs):
    """Call spin() to sync state prior to calling the method."""
    self.wait(0)
    if not self._ready:
        raise error.TimeoutError("result not ready")
    return f(self, *args, **kwargs)

class AsyncResult(object):
    """Class for representing results of non-blocking calls.

    Provides the same interface as :py:class:`multiprocessing.pool.AsyncResult`.
    """

    msg_ids = None
    _targets = None
    _tracker = None
    _single_result = False

    def __init__(self, client, msg_ids, fname='unknown', targets=None, tracker=None):
        if isinstance(msg_ids, basestring):
            # always a list
            msg_ids = [msg_ids]
        if tracker is None:
            # default to always done
            tracker = finished_tracker
        self._client = client
        self.msg_ids = msg_ids
        self._fname=fname
        self._targets = targets
        self._tracker = tracker
        self._ready = False
        self._success = None
        self._metadata = None
        if len(msg_ids) == 1:
            self._single_result = not isinstance(targets, (list, tuple))
        else:
            self._single_result = False

    def __repr__(self):
        if self._ready:
            return "<%s: finished>"%(self.__class__.__name__)
        else:
            return "<%s: %s>"%(self.__class__.__name__,self._fname)


    def _reconstruct_result(self, res):
        """Reconstruct our result from actual result list (always a list)

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
        by get() inside a `RemoteError`.
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

        This method always returns None.
        """
        if self._ready:
            return
        self._ready = self._client.wait(self.msg_ids, timeout)
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
        assert self.ready()
        return self._success

    #----------------------------------------------------------------
    # Extra methods not in mp.pool.AsyncResult
    #----------------------------------------------------------------

    def get_dict(self, timeout=-1):
        """Get the results as a dict, keyed by engine_id.

        timeout behavior is described in `get()`.
        """

        results = self.get(timeout)
        engine_ids = [ md['engine_id'] for md in self._metadata ]
        bycount = sorted(engine_ids, key=lambda k: engine_ids.count(k))
        maxcount = bycount.count(bycount[-1])
        if maxcount > 1:
            raise ValueError("Cannot build dict, %i jobs ran on engine #%i"%(
                    maxcount, bycount[-1]))

        return dict(zip(engine_ids,results))

    @property
    def result(self):
        """result property wrapper for `get(timeout=0)`."""
        return self.get()

    # abbreviated alias:
    r = result

    @property
    @check_ready
    def metadata(self):
        """property for accessing execution metadata."""
        if self._single_result:
            return self._metadata[0]
        else:
            return self._metadata

    @property
    def result_dict(self):
        """result property as a dict."""
        return self.get_dict()

    def __dict__(self):
        return self.get_dict(0)

    def abort(self):
        """abort my tasks."""
        assert not self.ready(), "Can't abort, I am already done!"
        return self.client.abort(self.msg_ids, targets=self._targets, block=True)

    @property
    def sent(self):
        """check whether my messages have been sent."""
        return self._tracker.done

    def wait_for_send(self, timeout=-1):
        """wait for pyzmq send to complete.

        This is necessary when sending arrays that you intend to edit in-place.
        `timeout` is in seconds, and will raise TimeoutError if it is reached
        before the send completes.
        """
        return self._tracker.wait(timeout)

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

    def __getattr__(self, key):
        """getattr maps to getitem for convenient attr access to metadata."""
        try:
            return self.__getitem__(key)
        except (error.TimeoutError, KeyError):
            raise AttributeError("%r object has no attribute %r"%(
                    self.__class__.__name__, key))

    # asynchronous iterator:
    def __iter__(self):
        if self._single_result:
            raise TypeError("AsyncResults with a single result are not iterable.")
        try:
            rlist = self.get(0)
        except error.TimeoutError:
            # wait for each result individually
            for msg_id in self.msg_ids:
                ar = AsyncResult(self._client, msg_id, self._fname)
                yield ar.get()
        else:
            # already done
            for r in rlist:
                yield r



class AsyncMapResult(AsyncResult):
    """Class for representing results of non-blocking gathers.

    This will properly reconstruct the gather.
    
    This class is iterable at any time, and will wait on results as they come.
    
    If ordered=False, then the first results to arrive will come first, otherwise
    results will be yielded in the order they were submitted.
    
    """

    def __init__(self, client, msg_ids, mapObject, fname='', ordered=True):
        AsyncResult.__init__(self, client, msg_ids, fname=fname)
        self._mapObject = mapObject
        self._single_result = False
        self.ordered = ordered

    def _reconstruct_result(self, res):
        """Perform the gather on the actual results."""
        return self._mapObject.joinPartitions(res)

    # asynchronous iterator:
    def __iter__(self):
        it = self._ordered_iter if self.ordered else self._unordered_iter
        for r in it():
            yield r

    # asynchronous ordered iterator:
    def _ordered_iter(self):
        """iterator for results *as they arrive*, preserving submission order."""
        try:
            rlist = self.get(0)
        except error.TimeoutError:
            # wait for each result individually
            for msg_id in self.msg_ids:
                ar = AsyncResult(self._client, msg_id, self._fname)
                rlist = ar.get()
                try:
                    for r in rlist:
                        yield r
                except TypeError:
                    # flattened, not a list
                    # this could get broken by flattened data that returns iterables
                    # but most calls to map do not expose the `flatten` argument
                    yield rlist
        else:
            # already done
            for r in rlist:
                yield r

    # asynchronous unordered iterator:
    def _unordered_iter(self):
        """iterator for results *as they arrive*, on FCFS basis, ignoring submission order."""
        try:
            rlist = self.get(0)
        except error.TimeoutError:
            pending = set(self.msg_ids)
            while pending:
                try:
                    self._client.wait(pending, 1e-3)
                except error.TimeoutError:
                    # ignore timeout error, because that only means
                    # *some* jobs are outstanding
                    pass
                # update ready set with those no longer outstanding:
                ready = pending.difference(self._client.outstanding)
                # update pending to exclude those that are finished
                pending = pending.difference(ready)
                while ready:
                    msg_id = ready.pop()
                    ar = AsyncResult(self._client, msg_id, self._fname)
                    rlist = ar.get()
                    try:
                        for r in rlist:
                            yield r
                    except TypeError:
                        # flattened, not a list
                        # this could get broken by flattened data that returns iterables
                        # but most calls to map do not expose the `flatten` argument
                        yield rlist
        else:
            # already done
            for r in rlist:
                yield r



class AsyncHubResult(AsyncResult):
    """Class to wrap pending results that must be requested from the Hub.

    Note that waiting/polling on these objects requires polling the Hubover the network,
    so use `AsyncHubResult.wait()` sparingly.
    """

    def wait(self, timeout=-1):
        """wait for result to complete."""
        start = time.time()
        if self._ready:
            return
        local_ids = filter(lambda msg_id: msg_id in self._client.outstanding, self.msg_ids)
        local_ready = self._client.wait(local_ids, timeout)
        if local_ready:
            remote_ids = filter(lambda msg_id: msg_id not in self._client.results, self.msg_ids)
            if not remote_ids:
                self._ready = True
            else:
                rdict = self._client.result_status(remote_ids, status_only=False)
                pending = rdict['pending']
                while pending and (timeout < 0 or time.time() < start+timeout):
                    rdict = self._client.result_status(remote_ids, status_only=False)
                    pending = rdict['pending']
                    if pending:
                        time.sleep(0.1)
                if not pending:
                    self._ready = True
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

__all__ = ['AsyncResult', 'AsyncMapResult', 'AsyncHubResult']