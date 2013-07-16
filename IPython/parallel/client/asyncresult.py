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

from __future__ import print_function

import sys
import time
from datetime import datetime

from zmq import MessageTracker

from IPython.core.display import clear_output, display, display_pretty
from IPython.external.decorator import decorator
from IPython.parallel import error

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def _total_seconds(td):
    """timedelta.total_seconds was added in 2.7"""
    try:
        # Python >= 2.7
        return td.total_seconds()
    except AttributeError:
        # Python 2.6
        return 1e-6 * (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6)

def _raw_text(s):
    display_pretty(s, raw=True)

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
            self._single_result = True
        else:
            self._single_result = False
        if tracker is None:
            # default to always done
            tracker = finished_tracker
        self._client = client
        self.msg_ids = msg_ids
        self._fname=fname
        self._targets = targets
        self._tracker = tracker
        
        self._ready = False
        self._outputs_ready = False
        self._success = None
        self._metadata = [ self._client.metadata.get(id) for id in self.msg_ids ]

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

    def _check_ready(self):
        if not self.ready():
            raise error.TimeoutError("Result not ready.")
    
    def ready(self):
        """Return whether the call has completed."""
        if not self._ready:
            self.wait(0)
        elif not self._outputs_ready:
            self._wait_for_outputs(0)
        
        return self._ready

    def wait(self, timeout=-1):
        """Wait until the result is available or until `timeout` seconds pass.

        This method always returns None.
        """
        if self._ready:
            self._wait_for_outputs(timeout)
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
            except Exception as e:
                self._exception = e
                self._success = False
            else:
                self._success = True
            finally:
                if timeout is None or timeout < 0:
                    # cutoff infinite wait at 10s
                    timeout = 10
                self._wait_for_outputs(timeout)


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
        if self._single_result:
            results = [results]
        engine_ids = [ md['engine_id'] for md in self._metadata ]
        
        
        rdict = {}
        for engine_id, result in zip(engine_ids, results):
            if engine_id in rdict:
                raise ValueError("Cannot build dict, %i jobs ran on engine #%i" % (
                    engine_ids.count(engine_id), engine_id)
                )
            else:
                rdict[engine_id] = result

        return rdict

    @property
    def result(self):
        """result property wrapper for `get(timeout=-1)`."""
        return self.get()

    # abbreviated alias:
    r = result

    @property
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
        return self._client.abort(self.msg_ids, targets=self._targets, block=True)

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

    def __getitem__(self, key):
        """getitem returns result value(s) if keyed by int/slice, or metadata if key is str.
        """
        if isinstance(key, int):
            self._check_ready()
            return error.collect_exceptions([self._result[key]], self._fname)[0]
        elif isinstance(key, slice):
            self._check_ready()
            return error.collect_exceptions(self._result[key], self._fname)
        elif isinstance(key, basestring):
            # metadata proxy *does not* require that results are done
            self.wait(0)
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
    
    def __len__(self):
        return len(self.msg_ids)
    
    #-------------------------------------
    # Sugar methods and attributes
    #-------------------------------------
    
    def timedelta(self, start, end, start_key=min, end_key=max):
        """compute the difference between two sets of timestamps
        
        The default behavior is to use the earliest of the first
        and the latest of the second list, but this can be changed
        by passing a different
        
        Parameters
        ----------
        
        start : one or more datetime objects (e.g. ar.submitted)
        end : one or more datetime objects (e.g. ar.received)
        start_key : callable
            Function to call on `start` to extract the relevant
            entry [defalt: min]
        end_key : callable
            Function to call on `end` to extract the relevant
            entry [default: max]
        
        Returns
        -------
        
        dt : float
            The time elapsed (in seconds) between the two selected timestamps.
        """
        if not isinstance(start, datetime):
            # handle single_result AsyncResults, where ar.stamp is single object,
            # not a list
            start = start_key(start)
        if not isinstance(end, datetime):
            # handle single_result AsyncResults, where ar.stamp is single object,
            # not a list
            end = end_key(end)
        return _total_seconds(end - start)
        
    @property
    def progress(self):
        """the number of tasks which have been completed at this point.
        
        Fractional progress would be given by 1.0 * ar.progress / len(ar)
        """
        self.wait(0)
        return len(self) - len(set(self.msg_ids).intersection(self._client.outstanding))
    
    @property
    def elapsed(self):
        """elapsed time since initial submission"""
        if self.ready():
            return self.wall_time
        
        now = submitted = datetime.now()
        for msg_id in self.msg_ids:
            if msg_id in self._client.metadata:
                stamp = self._client.metadata[msg_id]['submitted']
                if stamp and stamp < submitted:
                    submitted = stamp
        return _total_seconds(now-submitted)
    
    @property
    @check_ready
    def serial_time(self):
        """serial computation time of a parallel calculation
        
        Computed as the sum of (completed-started) of each task
        """
        t = 0
        for md in self._metadata:
            t += _total_seconds(md['completed'] - md['started'])
        return t
    
    @property
    @check_ready
    def wall_time(self):
        """actual computation time of a parallel calculation
        
        Computed as the time between the latest `received` stamp
        and the earliest `submitted`.
        
        Only reliable if Client was spinning/waiting when the task finished, because
        the `received` timestamp is created when a result is pulled off of the zmq queue,
        which happens as a result of `client.spin()`.
        
        For similar comparison of other timestamp pairs, check out AsyncResult.timedelta.
        
        """
        return self.timedelta(self.submitted, self.received)
    
    def wait_interactive(self, interval=1., timeout=-1):
        """interactive wait, printing progress at regular intervals"""
        if timeout is None:
            timeout = -1
        N = len(self)
        tic = time.time()
        while not self.ready() and (timeout < 0 or time.time() - tic <= timeout):
            self.wait(interval)
            clear_output()
            print("%4i/%i tasks finished after %4i s" % (self.progress, N, self.elapsed), end="")
            sys.stdout.flush()
        print()
        print("done")
    
    def _republish_displaypub(self, content, eid):
        """republish individual displaypub content dicts"""
        try:
            ip = get_ipython()
        except NameError:
            # displaypub is meaningless outside IPython
            return
        md = content['metadata'] or {}
        md['engine'] = eid
        ip.display_pub.publish(content['source'], content['data'], md)
    
    def _display_stream(self, text, prefix='', file=None):
        if not text:
            # nothing to display
            return
        if file is None:
            file = sys.stdout
        end = '' if text.endswith('\n') else '\n'
        
        multiline = text.count('\n') > int(text.endswith('\n'))
        if prefix and multiline and not text.startswith('\n'):
            prefix = prefix + '\n'
        print("%s%s" % (prefix, text), file=file, end=end)
        
    
    def _display_single_result(self):
        self._display_stream(self.stdout)
        self._display_stream(self.stderr, file=sys.stderr)
        
        try:
            get_ipython()
        except NameError:
            # displaypub is meaningless outside IPython
            return
        
        for output in self.outputs:
            self._republish_displaypub(output, self.engine_id)
        
        if self.pyout is not None:
            display(self.get())
    
    def _wait_for_outputs(self, timeout=-1):
        """wait for the 'status=idle' message that indicates we have all outputs
        """
        if self._outputs_ready or not self._success:
            # don't wait on errors
            return
        
        # cast None to -1 for infinite timeout
        if timeout is None:
            timeout = -1
        
        tic = time.time()
        while True:
            self._client._flush_iopub(self._client._iopub_socket)
            self._outputs_ready = all(md['outputs_ready']
                                      for md in self._metadata)
            if self._outputs_ready or \
               (timeout >= 0 and time.time() > tic + timeout):
                break
            time.sleep(0.01)
    
    @check_ready
    def display_outputs(self, groupby="type"):
        """republish the outputs of the computation
        
        Parameters
        ----------
        
        groupby : str [default: type]
            if 'type':
                Group outputs by type (show all stdout, then all stderr, etc.):
                
                [stdout:1] foo
                [stdout:2] foo
                [stderr:1] bar
                [stderr:2] bar
            if 'engine':
                Display outputs for each engine before moving on to the next:
                
                [stdout:1] foo
                [stderr:1] bar
                [stdout:2] foo
                [stderr:2] bar
                
            if 'order':
                Like 'type', but further collate individual displaypub
                outputs.  This is meant for cases of each command producing
                several plots, and you would like to see all of the first
                plots together, then all of the second plots, and so on.
        """
        if self._single_result:
            self._display_single_result()
            return
        
        stdouts = self.stdout
        stderrs = self.stderr
        pyouts  = self.pyout
        output_lists = self.outputs
        results = self.get()
        
        targets = self.engine_id
        
        if groupby == "engine":
            for eid,stdout,stderr,outputs,r,pyout in zip(
                    targets, stdouts, stderrs, output_lists, results, pyouts
                ):
                self._display_stream(stdout, '[stdout:%i] ' % eid)
                self._display_stream(stderr, '[stderr:%i] ' % eid, file=sys.stderr)
                
                try:
                    get_ipython()
                except NameError:
                    # displaypub is meaningless outside IPython
                    return 
                
                if outputs or pyout is not None:
                    _raw_text('[output:%i]' % eid)
                
                for output in outputs:
                    self._republish_displaypub(output, eid)
                
                if pyout is not None:
                    display(r)
        
        elif groupby in ('type', 'order'):
            # republish stdout:
            for eid,stdout in zip(targets, stdouts):
                self._display_stream(stdout, '[stdout:%i] ' % eid)
        
            # republish stderr:
            for eid,stderr in zip(targets, stderrs):
                self._display_stream(stderr, '[stderr:%i] ' % eid, file=sys.stderr)
        
            try:
                get_ipython()
            except NameError:
                # displaypub is meaningless outside IPython
                return
            
            if groupby == 'order':
                output_dict = dict((eid, outputs) for eid,outputs in zip(targets, output_lists))
                N = max(len(outputs) for outputs in output_lists)
                for i in range(N):
                    for eid in targets:
                        outputs = output_dict[eid]
                        if len(outputs) >= N:
                            _raw_text('[output:%i]' % eid)
                            self._republish_displaypub(outputs[i], eid)
            else:
                # republish displaypub output
                for eid,outputs in zip(targets, output_lists):
                    if outputs:
                        _raw_text('[output:%i]' % eid)
                    for output in outputs:
                        self._republish_displaypub(output, eid)
        
            # finally, add pyout:
            for eid,r,pyout in zip(targets, results, pyouts):
                if pyout is not None:
                    display(r)
        
        else:
            raise ValueError("groupby must be one of 'type', 'engine', 'collate', not %r" % groupby)
        
        


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

    def _wait_for_outputs(self, timeout=-1):
        """no-op, because HubResults are never incomplete"""
        self._outputs_ready = True
    
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
            except Exception as e:
                self._exception = e
                self._success = False
            else:
                self._success = True
            finally:
                self._metadata = map(self._client.metadata.get, self.msg_ids)

__all__ = ['AsyncResult', 'AsyncMapResult', 'AsyncHubResult']
