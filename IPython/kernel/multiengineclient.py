# encoding: utf-8
# -*- test-case-name: IPython.kernel.test.test_multiengineclient -*-

"""General Classes for IMultiEngine clients."""

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

import sys
import cPickle as pickle
from types import FunctionType
import linecache

from twisted.internet import reactor
from twisted.python import components, log
from twisted.python.failure import Failure
from zope.interface import Interface, implements, Attribute

from IPython.ColorANSI import TermColors

from IPython.kernel.twistedutil import blockingCallFromThread
from IPython.kernel import error
from IPython.kernel.parallelfunction import ParallelFunction
from IPython.kernel.mapper import (
    MultiEngineMapper, 
    IMultiEngineMapperFactory,
    IMapper
)
from IPython.kernel import map as Map
from IPython.kernel import multiengine as me
from IPython.kernel.multiengine import (IFullMultiEngine,
    IFullSynchronousMultiEngine)


#-------------------------------------------------------------------------------
# Pending Result things
#-------------------------------------------------------------------------------

class IPendingResult(Interface):
    """A representation of a result that is pending.
    
    This class is similar to Twisted's `Deferred` object, but is designed to be
    used in a synchronous context.
    """
    
    result_id=Attribute("ID of the deferred on the other side")
    client=Attribute("A client that I came from")
    r=Attribute("An attribute that is a property that calls and returns get_result")
    
    def get_result(default=None, block=True):
        """
        Get a result that is pending.
                
        :Parameters:
            default
                The value to return if the result is not ready.
            block : boolean
                Should I block for the result.
                
        :Returns: The actual result or the default value.
        """
        
    def add_callback(f, *args, **kwargs):
        """
        Add a callback that is called with the result.
        
        If the original result is foo, adding a callback will cause
        f(foo, *args, **kwargs) to be returned instead.  If multiple
        callbacks are registered, they are chained together: the result of
        one is passed to the next and so on.  
        
        Unlike Twisted's Deferred object, there is no errback chain.  Thus
        any exception raised will not be caught and handled.  User must 
        catch these by hand when calling `get_result`.
        """


class PendingResult(object):
    """A representation of a result that is not yet ready.
    
    A user should not create a `PendingResult` instance by hand.
    
    Methods
    =======
    
    * `get_result`
    * `add_callback`
    
    Properties
    ==========
    * `r`
    """
    
    def __init__(self, client, result_id):
        """Create a PendingResult with a result_id and a client instance.
        
        The client should implement `_getPendingResult(result_id, block)`.
        """
        self.client = client
        self.result_id = result_id
        self.called = False
        self.raised = False
        self.callbacks = []
        
    def get_result(self, default=None, block=True):
        """Get a result that is pending.
                
        This method will connect to an IMultiEngine adapted controller
        and see if the result is ready.  If the action triggers an exception
        raise it and record it.  This method records the result/exception once it is 
        retrieved.  Calling `get_result` again will get this cached result or will
        re-raise the exception.  The .r attribute is a property that calls
        `get_result` with block=True.
        
        :Parameters:
            default
                The value to return if the result is not ready.
            block : boolean
                Should I block for the result.
                
        :Returns: The actual result or the default value.
        """
        
        if self.called:
            if self.raised:
                raise self.result[0], self.result[1], self.result[2]
            else:
                return self.result
        try:
            result = self.client.get_pending_deferred(self.result_id, block)
        except error.ResultNotCompleted:
            return default
        except:
            # Reraise other error, but first record them so they can be reraised
            # later if .r or get_result is called again.
            self.result = sys.exc_info()
            self.called = True
            self.raised = True
            raise
        else:
            for cb in self.callbacks:
                result = cb[0](result, *cb[1], **cb[2])
            self.result = result
            self.called = True
            return result
        
    def add_callback(self, f, *args, **kwargs):
        """Add a callback that is called with the result.
        
        If the original result is result, adding a callback will cause
        f(result, *args, **kwargs) to be returned instead.  If multiple
        callbacks are registered, they are chained together: the result of
        one is passed to the next and so on.  
        
        Unlike Twisted's Deferred object, there is no errback chain.  Thus
        any exception raised will not be caught and handled.  User must 
        catch these by hand when calling `get_result`.
        """
        assert callable(f)
        self.callbacks.append((f, args, kwargs))
        
    def __cmp__(self, other):
        if self.result_id < other.result_id:
            return -1
        else:
            return 1
            
    def _get_r(self):
        return self.get_result(block=True)
    
    r = property(_get_r)
    """This property is a shortcut to a `get_result(block=True)`."""


#-------------------------------------------------------------------------------
# Pretty printing wrappers for certain lists
#-------------------------------------------------------------------------------    
    
class ResultList(list):
    """A subclass of list that pretty prints the output of `execute`/`get_result`."""
    
    def __repr__(self):
        output = []
        # These colored prompts were not working on Windows
        if sys.platform == 'win32':
            blue = normal = red = green = ''
        else:
            blue = TermColors.Blue
            normal = TermColors.Normal
            red = TermColors.Red
            green = TermColors.Green
        output.append("<Results List>\n")
        for cmd in self:
            if isinstance(cmd, Failure):
                output.append(cmd)
            else:
                target = cmd.get('id',None)
                cmd_num = cmd.get('number',None)
                cmd_stdin = cmd.get('input',{}).get('translated','No Input')
                cmd_stdout = cmd.get('stdout', None)
                cmd_stderr = cmd.get('stderr', None)
                output.append("%s[%i]%s In [%i]:%s %s\n" % \
                    (green, target,
                    blue, cmd_num, normal, cmd_stdin))
                if cmd_stdout:
                    output.append("%s[%i]%s Out[%i]:%s %s\n" % \
                        (green, target,
                        red, cmd_num, normal, cmd_stdout))
                if cmd_stderr:
                    output.append("%s[%i]%s Err[%i]:\n%s %s" % \
                        (green, target,
                        red, cmd_num, normal, cmd_stderr))
        return ''.join(output)


def wrapResultList(result):
    """A function that wraps the output of `execute`/`get_result` -> `ResultList`."""
    if len(result) == 0:
        result = [result]
    return ResultList(result)


class QueueStatusList(list):
    """A subclass of list that pretty prints the output of `queue_status`."""
    
    def __repr__(self):
        output = []
        output.append("<Queue Status List>\n")
        for e in self:
            output.append("Engine: %s\n" % repr(e[0]))
            output.append("    Pending: %s\n" % repr(e[1]['pending']))
            for q in e[1]['queue']:
                output.append("    Command: %s\n" % repr(q))
        return ''.join(output)


#-------------------------------------------------------------------------------
# InteractiveMultiEngineClient
#-------------------------------------------------------------------------------    

class InteractiveMultiEngineClient(object):
    """A mixin class that add a few methods to a multiengine client.
    
    The methods in this mixin class are designed for interactive usage.
    """
                                        
    def activate(self):
        """Make this `MultiEngineClient` active for parallel magic commands.
        
        IPython has a magic command syntax to work with `MultiEngineClient` objects.
        In a given IPython session there is a single active one.  While
        there can be many `MultiEngineClient` created and used by the user, 
        there is only one active one.  The active `MultiEngineClient` is used whenever 
        the magic commands %px and %autopx are used.
        
        The activate() method is called on a given `MultiEngineClient` to make it 
        active.  Once this has been done, the magic commands can be used.
        """
        
        try:
            __IPYTHON__.activeController = self
        except NameError:
            print "The IPython Controller magics only work within IPython."
                    
    def __setitem__(self, key, value):
        """Add a dictionary interface for pushing/pulling.
        
        This functions as a shorthand for `push`.
        
        :Parameters:
            key : str 
                What to call the remote object.
            value : object
                The local Python object to push.
        """
        targets, block = self._findTargetsAndBlock()
        return self.push({key:value}, targets=targets, block=block)
    
    def __getitem__(self, key):
        """Add a dictionary interface for pushing/pulling.
        
        This functions as a shorthand to `pull`.
        
        :Parameters:
         - `key`: A string representing the key.
        """
        if isinstance(key, str):
            targets, block = self._findTargetsAndBlock()
            return self.pull(key, targets=targets, block=block)
        else:
            raise TypeError("__getitem__ only takes strs")
            
    def __len__(self):
        """Return the number of available engines."""
        return len(self.get_ids())
    
    #---------------------------------------------------------------------------
    # Make this a context manager for with
    #---------------------------------------------------------------------------
    
    def findsource_file(self,f):
        linecache.checkcache()
        s = findsource(f.f_code)
        lnum = f.f_lineno
        wsource = s[0][f.f_lineno:]
        return strip_whitespace(wsource)

    def findsource_ipython(self,f):
        from IPython import ipapi
        self.ip = ipapi.get()
        wsource = [l+'\n' for l in
                   self.ip.IP.input_hist_raw[-1].splitlines()[1:]] 
        return strip_whitespace(wsource)
        
    def __enter__(self):
        f = sys._getframe(1)
        local_ns = f.f_locals
        global_ns = f.f_globals
        if f.f_code.co_filename == '<ipython console>':
            s = self.findsource_ipython(f)
        else:
            s = self.findsource_file(f)

        self._with_context_result = self.execute(s)

    def __exit__ (self, etype, value, tb):
        if issubclass(etype,error.StopLocalExecution):
            return True


def remote():
    m = 'Special exception to stop local execution of parallel code.'
    raise error.StopLocalExecution(m)

def strip_whitespace(source):
    # Expand tabs to avoid any confusion.
    wsource = [l.expandtabs(4) for l in source]
    # Detect the indentation level
    done = False
    for line in wsource:
        if line.isspace():
            continue
        for col,char in enumerate(line):
            if char != ' ':
                done = True
                break
        if done:
            break
    # Now we know how much leading space there is in the code.  Next, we
    # extract up to the first line that has less indentation.
    # WARNINGS: we skip comments that may be misindented, but we do NOT yet
    # detect triple quoted strings that may have flush left text.
    for lno,line in enumerate(wsource):
        lead = line[:col]
        if lead.isspace():
            continue
        else:
            if not lead.lstrip().startswith('#'):
                break
    # The real 'with' source is up to lno
    src_lines = [l[col:] for l in wsource[:lno+1]]

    # Finally, check that the source's first non-comment line begins with the
    # special call 'remote()'
    for nline,line in enumerate(src_lines):
        if line.isspace() or line.startswith('#'):
            continue
        if 'remote()' in line:
            break
        else:
            raise ValueError('remote() call missing at the start of code')
    src = ''.join(src_lines[nline+1:])
    #print 'SRC:\n<<<<<<<>>>>>>>\n%s<<<<<>>>>>>' % src  # dbg
    return src


#-------------------------------------------------------------------------------
# The top-level MultiEngine client adaptor
#-------------------------------------------------------------------------------


class IFullBlockingMultiEngineClient(Interface):
    pass


class FullBlockingMultiEngineClient(InteractiveMultiEngineClient):
    """
    A blocking client to the `IMultiEngine` controller interface.
    
    This class allows users to use a set of engines for a parallel
    computation through the `IMultiEngine` interface.  In this interface,
    each engine has a specific id (an int) that is used to refer to the
    engine, run code on it, etc.
    """
    
    implements(
        IFullBlockingMultiEngineClient,
        IMultiEngineMapperFactory,
        IMapper
    )
    
    def __init__(self, smultiengine):
        self.smultiengine = smultiengine
        self.block = True
        self.targets = 'all'
    
    def _findBlock(self, block=None):
        if block is None:
            return self.block
        else:
            if block in (True, False):
                return block
            else:
                raise ValueError("block must be True or False")
    
    def _findTargets(self, targets=None):
        if targets is None:
            return self.targets
        else:
            if not isinstance(targets, (str,list,tuple,int)):
                raise ValueError("targets must be a str, list, tuple or int")
            return targets
    
    def _findTargetsAndBlock(self, targets=None, block=None):
        return self._findTargets(targets), self._findBlock(block) 
    
    def _blockFromThread(self, function, *args, **kwargs):
        block = kwargs.get('block', None)
        if block is None:
            raise error.MissingBlockArgument("'block' keyword argument is missing")
        result = blockingCallFromThread(function, *args, **kwargs)
        if not block:
            result = PendingResult(self, result)
        return result
    
    def get_pending_deferred(self, deferredID, block):
        return blockingCallFromThread(self.smultiengine.get_pending_deferred, deferredID, block)
    
    def barrier(self, pendingResults):
        """Synchronize a set of `PendingResults`.
        
        This method is a synchronization primitive that waits for a set of
        `PendingResult` objects to complete.  More specifically, barier does
        the following.
        
        * The `PendingResult`s are sorted by result_id.
        * The `get_result` method is called for each `PendingResult` sequentially
          with block=True.
        * If a `PendingResult` gets a result that is an exception, it is 
          trapped and can be re-raised later by calling `get_result` again.
        * The `PendingResult`s are flushed from the controller.
                
        After barrier has been called on a `PendingResult`, its results can 
        be retrieved by calling `get_result` again or accesing the `r` attribute
        of the instance.
        """
        
        # Convert to list for sorting and check class type 
        prList = list(pendingResults)
        for pr in prList:
            if not isinstance(pr, PendingResult):
                raise error.NotAPendingResult("Objects passed to barrier must be PendingResult instances")
                            
        # Sort the PendingResults so they are in order
        prList.sort()
        # Block on each PendingResult object
        for pr in prList:
            try:
                result = pr.get_result(block=True)
            except Exception:
                pass
    
    def flush(self):
        """
        Clear all pending deferreds/results from the controller.
        
        For each `PendingResult` that is created by this client, the controller
        holds on to the result for that `PendingResult`.  This can be a problem
        if there are a large number of `PendingResult` objects that are created.
        
        Once the result of the `PendingResult` has been retrieved, the result
        is removed from the controller, but if a user doesn't get a result (
        they just ignore the `PendingResult`) the result is kept forever on the
        controller.  This method allows the user to clear out all un-retrieved
        results on the controller. 
        """
        r = blockingCallFromThread(self.smultiengine.clear_pending_deferreds)
        return r
    
    clear_pending_results = flush
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def execute(self, lines, targets=None, block=None):
        """
        Execute code on a set of engines.
        
        :Parameters:
            lines : str
                The Python code to execute as a string
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        result = blockingCallFromThread(self.smultiengine.execute, lines,
            targets=targets, block=block)
        if block:
            result = ResultList(result)
        else:
            result = PendingResult(self, result)
            result.add_callback(wrapResultList)
        return result
    
    def push(self, namespace, targets=None, block=None):
        """
        Push a dictionary of keys and values to engines namespace.
        
        Each engine has a persistent namespace.  This method is used to push
        Python objects into that namespace.
        
        The objects in the namespace must be pickleable.
        
        :Parameters:
            namespace : dict
                A dict that contains Python objects to be injected into
                the engine persistent namespace.
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.push, namespace,
            targets=targets, block=block)
    
    def pull(self, keys, targets=None, block=None):
        """
        Pull Python objects by key out of engines namespaces.
        
        :Parameters:
            keys : str or list of str
                The names of the variables to be pulled
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.pull, keys, targets=targets, block=block)
    
    def push_function(self, namespace, targets=None, block=None):
        """
        Push a Python function to an engine.
        
        This method is used to push a Python function to an engine.  This
        method can then be used in code on the engines.  Closures are not supported.
        
        :Parameters:
            namespace : dict
                A dict whose values are the functions to be pushed.  The keys give
                that names that the function will appear as in the engines
                namespace.
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.push_function, namespace, targets=targets, block=block)
    
    def pull_function(self, keys, targets=None, block=None):
        """
        Pull a Python function from an engine.
        
        This method is used to pull a Python function from an engine.
        Closures are not supported.
        
        :Parameters:
            keys : str or list of str
                The names of the functions to be pulled
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.pull_function, keys, targets=targets, block=block)
    
    def push_serialized(self, namespace, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.push_serialized, namespace, targets=targets, block=block)
    
    def pull_serialized(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.pull_serialized, keys, targets=targets, block=block)
    
    def get_result(self, i=None, targets=None, block=None):
        """
        Get a previous result.
        
        When code is executed in an engine, a dict is created and returned.  This
        method retrieves that dict for previous commands.
        
        :Parameters:
            i : int
                The number of the result to get
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        result = blockingCallFromThread(self.smultiengine.get_result, i, targets=targets, block=block)
        if block:
            result = ResultList(result)
        else:
            result = PendingResult(self, result)
            result.add_callback(wrapResultList)
        return result
    
    def reset(self, targets=None, block=None):
        """
        Reset an engine.
        
        This method clears out the namespace of an engine.

        :Parameters:
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.reset, targets=targets, block=block)
    
    def keys(self, targets=None, block=None):
        """
        Get a list of all the variables in an engine's namespace.

        :Parameters:
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.keys, targets=targets, block=block)
    
    def kill(self, controller=False, targets=None, block=None):
        """
        Kill the engines and controller.
        
        This method is used to stop the engine and controller by calling
        `reactor.stop`.
        
        :Parameters:
            controller : boolean
                If True, kill the engines and controller.  If False, just the 
                engines
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.kill, controller, targets=targets, block=block)
    
    def clear_queue(self, targets=None, block=None):
        """
        Clear out the controller's queue for an engine.
        
        The controller maintains a queue for each engine.  This clear it out.
        
        :Parameters:
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.clear_queue, targets=targets, block=block)
    
    def queue_status(self, targets=None, block=None):
        """
        Get the status of an engines queue.
        
        :Parameters:
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.queue_status, targets=targets, block=block)
    
    def set_properties(self, properties, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.set_properties, properties, targets=targets, block=block)
    
    def get_properties(self, keys=None, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.get_properties, keys, targets=targets, block=block)
    
    def has_properties(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.has_properties, keys, targets=targets, block=block)
    
    def del_properties(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.del_properties, keys, targets=targets, block=block)
    
    def clear_properties(self, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.clear_properties, targets=targets, block=block)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def get_ids(self):
        """
        Returns the ids of currently registered engines.
        """
        result = blockingCallFromThread(self.smultiengine.get_ids)
        return result
        
    #---------------------------------------------------------------------------
    # IMultiEngineCoordinator
    #---------------------------------------------------------------------------
             
    def scatter(self, key, seq, dist='b', flatten=False, targets=None, block=None):
        """
        Partition a Python sequence and send the partitions to a set of engines.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.scatter, key, seq, 
            dist, flatten, targets=targets, block=block)
    
    def gather(self, key, dist='b', targets=None, block=None):
        """
        Gather a partitioned sequence on a set of engines as a single local seq.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.gather, key, dist, 
            targets=targets, block=block)
    
    def raw_map(self, func, seq, dist='b', targets=None, block=None):
        """
        A parallelized version of Python's builtin map.
        
        This has a slightly different syntax than the builtin `map`.
        This is needed because we need to have keyword arguments and thus
        can't use *args to capture all the sequences.  Instead, they must
        be passed in a list or tuple.
        
        raw_map(func, seqs) -> map(func, seqs[0], seqs[1], ...)
        
        Most users will want to use parallel functions or the `mapper`
        and `map` methods for an API that follows that of the builtin
        `map`.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.raw_map, func, seq, 
            dist, targets=targets, block=block)
    
    def map(self, func, *sequences):
        """
        A parallel version of Python's builtin `map` function.
        
        This method applies a function to sequences of arguments.  It 
        follows the same syntax as the builtin `map`.
        
        This method creates a mapper objects by calling `self.mapper` with
        no arguments and then uses that mapper to do the mapping.  See
        the documentation of `mapper` for more details.
        """
        return self.mapper().map(func, *sequences)
    
    def mapper(self, dist='b', targets='all', block=None):
        """
        Create a mapper object that has a `map` method.
        
        This method returns an object that implements the `IMapper` 
        interface.  This method is a factory that is used to control how 
        the map happens.
        
        :Parameters:
            dist : str
                What decomposition to use, 'b' is the only one supported
                currently
            targets : str, int, sequence of ints
                Which engines to use for the map
            block : boolean
                Should calls to `map` block or not
        """
        return MultiEngineMapper(self, dist, targets, block)
    
    def parallel(self, dist='b', targets=None, block=None):
        """
        A decorator that turns a function into a parallel function.
        
        This can be used as:
        
        @parallel()
        def f(x, y)
            ...
        
        f(range(10), range(10))
        
        This causes f(0,0), f(1,1), ... to be called in parallel.
        
        :Parameters:
            dist : str
                What decomposition to use, 'b' is the only one supported
                currently
            targets : str, int, sequence of ints
                Which engines to use for the map
            block : boolean
                Should calls to `map` block or not
        """
        targets, block = self._findTargetsAndBlock(targets, block)       
        mapper = self.mapper(dist, targets, block)
        pf = ParallelFunction(mapper)
        return pf
    
    #---------------------------------------------------------------------------
    # IMultiEngineExtras
    #---------------------------------------------------------------------------
    
    def zip_pull(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.zip_pull, keys, 
            targets=targets, block=block)
    
    def run(self, filename, targets=None, block=None):
        """
        Run a Python code in a file on the engines.
        
        :Parameters:
            filename : str
                The name of the local file to run
            targets : id or list of ids
                The engine to use for the execution
            block : boolean
                If False, this method will return the actual result.  If False,
                a `PendingResult` is returned which can be used to get the result
                at a later time.
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.run, filename,
            targets=targets, block=block)



components.registerAdapter(FullBlockingMultiEngineClient,
            IFullSynchronousMultiEngine, IFullBlockingMultiEngineClient)




