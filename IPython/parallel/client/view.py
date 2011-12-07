"""Views of remote engines.

Authors:

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

import imp
import sys
import warnings
from contextlib import contextmanager
from types import ModuleType

import zmq

from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.traitlets import (
    HasTraits, Any, Bool, List, Dict, Set, Instance, CFloat, Integer
)
from IPython.external.decorator import decorator

from IPython.parallel import util
from IPython.parallel.controller.dependency import Dependency, dependent

from . import map as Map
from .asyncresult import AsyncResult, AsyncMapResult
from .remotefunction import ParallelFunction, parallel, remote

#-----------------------------------------------------------------------------
# Decorators
#-----------------------------------------------------------------------------

@decorator
def save_ids(f, self, *args, **kwargs):
    """Keep our history and outstanding attributes up to date after a method call."""
    n_previous = len(self.client.history)
    try:
        ret = f(self, *args, **kwargs)
    finally:
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

@skip_doctest
class View(HasTraits):
    """Base View class for more convenint apply(f,*args,**kwargs) syntax via attributes.

    Don't use this class, use subclasses.

    Methods
    -------

    spin
        flushes incoming results and registration state changes
        control methods spin, and requesting `ids` also ensures up to date

    wait
        wait on one or more msg_ids

    execution methods
        apply
        legacy: execute, run

    data movement
        push, pull, scatter, gather

    query methods
        get_result, queue_status, purge_results, result_status

    control methods
        abort, shutdown

    """
    # flags
    block=Bool(False)
    track=Bool(True)
    targets = Any()

    history=List()
    outstanding = Set()
    results = Dict()
    client = Instance('IPython.parallel.Client')

    _socket = Instance('zmq.Socket')
    _flag_names = List(['targets', 'block', 'track'])
    _targets = Any()
    _idents = Any()

    def __init__(self, client=None, socket=None, **flags):
        super(View, self).__init__(client=client, _socket=socket)
        self.block = client.block

        self.set_flags(**flags)

        assert not self.__class__ is View, "Don't use base View objects, use subclasses"


    def __repr__(self):
        strtargets = str(self.targets)
        if len(strtargets) > 16:
            strtargets = strtargets[:12]+'...]'
        return "<%s %s>"%(self.__class__.__name__, strtargets)

    def set_flags(self, **kwargs):
        """set my attribute flags by keyword.

        Views determine behavior with a few attributes (`block`, `track`, etc.).
        These attributes can be set all at once by name with this method.

        Parameters
        ----------

        block : bool
            whether to wait for results
        track : bool
            whether to create a MessageTracker to allow the user to
            safely edit after arrays and buffers during non-copying
            sends.
        """
        for name, value in kwargs.iteritems():
            if name not in self._flag_names:
                raise KeyError("Invalid name: %r"%name)
            else:
                setattr(self, name, value)

    @contextmanager
    def temp_flags(self, **kwargs):
        """temporarily set flags, for use in `with` statements.

        See set_flags for permanent setting of flags

        Examples
        --------

        >>> view.track=False
        ...
        >>> with view.temp_flags(track=True):
        ...    ar = view.apply(dostuff, my_big_array)
        ...    ar.tracker.wait() # wait for send to finish
        >>> view.track
        False

        """
        # preflight: save flags, and set temporaries
        saved_flags = {}
        for f in self._flag_names:
            saved_flags[f] = getattr(self, f)
        self.set_flags(**kwargs)
        # yield to the with-statement block
        try:
            yield
        finally:
            # postflight: restore saved flags
            self.set_flags(**saved_flags)


    #----------------------------------------------------------------
    # apply
    #----------------------------------------------------------------

    @sync_results
    @save_ids
    def _really_apply(self, f, args, kwargs, block=None, **options):
        """wrapper for client.send_apply_message"""
        raise NotImplementedError("Implement in subclasses")

    def apply(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) on remote engines, returning the result.

        This method sets all apply flags via this View's attributes.

        if self.block is False:
            returns AsyncResult
        else:
            returns actual result of f(*args, **kwargs)
        """
        return self._really_apply(f, args, kwargs)

    def apply_async(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) on remote engines in a nonblocking manner.

        returns AsyncResult
        """
        return self._really_apply(f, args, kwargs, block=False)

    @spin_after
    def apply_sync(self, f, *args, **kwargs):
        """calls f(*args, **kwargs) on remote engines in a blocking manner,
         returning the result.

        returns: actual result of f(*args, **kwargs)
        """
        return self._really_apply(f, args, kwargs, block=True)

    #----------------------------------------------------------------
    # wrappers for client and control methods
    #----------------------------------------------------------------
    @sync_results
    def spin(self):
        """spin the client, and sync"""
        self.client.spin()

    @sync_results
    def wait(self, jobs=None, timeout=-1):
        """waits on one or more `jobs`, for up to `timeout` seconds.

        Parameters
        ----------

        jobs : int, str, or list of ints and/or strs, or one or more AsyncResult objects
                ints are indices to self.history
                strs are msg_ids
                default: wait on all outstanding messages
        timeout : float
                a time in seconds, after which to give up.
                default is -1, which means no timeout

        Returns
        -------

        True : when all msg_ids are done
        False : timeout reached, some msg_ids still outstanding
        """
        if jobs is None:
            jobs = self.history
        return self.client.wait(jobs, timeout)

    def abort(self, jobs=None, targets=None, block=None):
        """Abort jobs on my engines.

        Parameters
        ----------

        jobs : None, str, list of strs, optional
            if None: abort all jobs.
            else: abort specific msg_id(s).
        """
        block = block if block is not None else self.block
        targets = targets if targets is not None else self.targets
        jobs = jobs if jobs is not None else list(self.outstanding)
        
        return self.client.abort(jobs=jobs, targets=targets, block=block)

    def queue_status(self, targets=None, verbose=False):
        """Fetch the Queue status of my engines"""
        targets = targets if targets is not None else self.targets
        return self.client.queue_status(targets=targets, verbose=verbose)

    def purge_results(self, jobs=[], targets=[]):
        """Instruct the controller to forget specific results."""
        if targets is None or targets == 'all':
            targets = self.targets
        return self.client.purge_results(jobs=jobs, targets=targets)

    def shutdown(self, targets=None, restart=False, hub=False, block=None):
        """Terminates one or more engine processes, optionally including the hub.
        """
        block = self.block if block is None else block
        if targets is None or targets == 'all':
            targets = self.targets
        return self.client.shutdown(targets=targets, restart=restart, hub=hub, block=block)

    @spin_after
    def get_result(self, indices_or_msg_ids=None):
        """return one or more results, specified by history index or msg_id.

        See client.get_result for details.

        """

        if indices_or_msg_ids is None:
            indices_or_msg_ids = -1
        if isinstance(indices_or_msg_ids, int):
            indices_or_msg_ids = self.history[indices_or_msg_ids]
        elif isinstance(indices_or_msg_ids, (list,tuple,set)):
            indices_or_msg_ids = list(indices_or_msg_ids)
            for i,index in enumerate(indices_or_msg_ids):
                if isinstance(index, int):
                    indices_or_msg_ids[i] = self.history[index]
        return self.client.get_result(indices_or_msg_ids)

    #-------------------------------------------------------------------
    # Map
    #-------------------------------------------------------------------

    def map(self, f, *sequences, **kwargs):
        """override in subclasses"""
        raise NotImplementedError

    def map_async(self, f, *sequences, **kwargs):
        """Parallel version of builtin `map`, using this view's engines.

        This is equivalent to map(...block=False)

        See `self.map` for details.
        """
        if 'block' in kwargs:
            raise TypeError("map_async doesn't take a `block` keyword argument.")
        kwargs['block'] = False
        return self.map(f,*sequences,**kwargs)

    def map_sync(self, f, *sequences, **kwargs):
        """Parallel version of builtin `map`, using this view's engines.

        This is equivalent to map(...block=True)

        See `self.map` for details.
        """
        if 'block' in kwargs:
            raise TypeError("map_sync doesn't take a `block` keyword argument.")
        kwargs['block'] = True
        return self.map(f,*sequences,**kwargs)

    def imap(self, f, *sequences, **kwargs):
        """Parallel version of `itertools.imap`.

        See `self.map` for details.

        """

        return iter(self.map_async(f,*sequences, **kwargs))

    #-------------------------------------------------------------------
    # Decorators
    #-------------------------------------------------------------------

    def remote(self, block=True, **flags):
        """Decorator for making a RemoteFunction"""
        block = self.block if block is None else block
        return remote(self, block=block, **flags)

    def parallel(self, dist='b', block=None, **flags):
        """Decorator for making a ParallelFunction"""
        block = self.block if block is None else block
        return parallel(self, dist=dist, block=block, **flags)

@skip_doctest
class DirectView(View):
    """Direct Multiplexer View of one or more engines.

    These are created via indexed access to a client:

    >>> dv_1 = client[1]
    >>> dv_all = client[:]
    >>> dv_even = client[::2]
    >>> dv_some = client[1:3]

    This object provides dictionary access to engine namespaces:

    # push a=5:
    >>> dv['a'] = 5
    # pull 'foo':
    >>> db['foo']

    """

    def __init__(self, client=None, socket=None, targets=None):
        super(DirectView, self).__init__(client=client, socket=socket, targets=targets)

    @property
    def importer(self):
        """sync_imports(local=True) as a property.

        See sync_imports for details.

        """
        return self.sync_imports(True)

    @contextmanager
    def sync_imports(self, local=True):
        """Context Manager for performing simultaneous local and remote imports.

        'import x as y' will *not* work.  The 'as y' part will simply be ignored.

        >>> with view.sync_imports():
        ...    from numpy import recarray
        importing recarray from numpy on engine(s)

        """
        import __builtin__
        local_import = __builtin__.__import__
        modules = set()
        results = []
        @util.interactive
        def remote_import(name, fromlist, level):
            """the function to be passed to apply, that actually performs the import
            on the engine, and loads up the user namespace.
            """
            import sys
            user_ns = globals()
            mod = __import__(name, fromlist=fromlist, level=level)
            if fromlist:
                for key in fromlist:
                    user_ns[key] = getattr(mod, key)
            else:
                user_ns[name] = sys.modules[name]

        def view_import(name, globals={}, locals={}, fromlist=[], level=-1):
            """the drop-in replacement for __import__, that optionally imports
            locally as well.
            """
            # don't override nested imports
            save_import = __builtin__.__import__
            __builtin__.__import__ = local_import

            if imp.lock_held():
                # this is a side-effect import, don't do it remotely, or even
                # ignore the local effects
                return local_import(name, globals, locals, fromlist, level)

            imp.acquire_lock()
            if local:
                mod = local_import(name, globals, locals, fromlist, level)
            else:
                raise NotImplementedError("remote-only imports not yet implemented")
            imp.release_lock()

            key = name+':'+','.join(fromlist or [])
            if level == -1 and key not in modules:
                modules.add(key)
                if fromlist:
                    print "importing %s from %s on engine(s)"%(','.join(fromlist), name)
                else:
                    print "importing %s on engine(s)"%name
                results.append(self.apply_async(remote_import, name, fromlist, level))
            # restore override
            __builtin__.__import__ = save_import

            return mod

        # override __import__
        __builtin__.__import__ = view_import
        try:
            # enter the block
            yield
        except ImportError:
            if not local:
                # ignore import errors if not doing local imports
                pass
        finally:
            # always restore __import__
            __builtin__.__import__ = local_import

        for r in results:
            # raise possible remote ImportErrors here
            r.get()


    @sync_results
    @save_ids
    def _really_apply(self, f, args=None, kwargs=None, targets=None, block=None, track=None):
        """calls f(*args, **kwargs) on remote engines, returning the result.

        This method sets all of `apply`'s flags via this View's attributes.

        Parameters
        ----------

        f : callable

        args : list [default: empty]

        kwargs : dict [default: empty]

        targets : target list [default: self.targets]
            where to run
        block : bool [default: self.block]
            whether to block
        track : bool [default: self.track]
            whether to ask zmq to track the message, for safe non-copying sends

        Returns
        -------

        if self.block is False:
            returns AsyncResult
        else:
            returns actual result of f(*args, **kwargs) on the engine(s)
            This will be a list of self.targets is also a list (even length 1), or
            the single result if self.targets is an integer engine id
        """
        args = [] if args is None else args
        kwargs = {} if kwargs is None else kwargs
        block = self.block if block is None else block
        track = self.track if track is None else track
        targets = self.targets if targets is None else targets

        _idents = self.client._build_targets(targets)[0]
        msg_ids = []
        trackers = []
        for ident in _idents:
            msg = self.client.send_apply_message(self._socket, f, args, kwargs, track=track,
                                    ident=ident)
            if track:
                trackers.append(msg['tracker'])
            msg_ids.append(msg['header']['msg_id'])
        tracker = None if track is False else zmq.MessageTracker(*trackers)
        ar = AsyncResult(self.client, msg_ids, fname=f.__name__, targets=targets, tracker=tracker)
        if block:
            try:
                return ar.get()
            except KeyboardInterrupt:
                pass
        return ar

    @spin_after
    def map(self, f, *sequences, **kwargs):
        """view.map(f, *sequences, block=self.block) => list|AsyncMapResult

        Parallel version of builtin `map`, using this View's `targets`.

        There will be one task per target, so work will be chunked
        if the sequences are longer than `targets`.

        Results can be iterated as they are ready, but will become available in chunks.

        Parameters
        ----------

        f : callable
            function to be mapped
        *sequences: one or more sequences of matching length
            the sequences to be distributed and passed to `f`
        block : bool
            whether to wait for the result or not [default self.block]

        Returns
        -------

        if block=False:
            AsyncMapResult
                An object like AsyncResult, but which reassembles the sequence of results
                into a single list. AsyncMapResults can be iterated through before all
                results are complete.
        else:
            list
                the result of map(f,*sequences)
        """

        block = kwargs.pop('block', self.block)
        for k in kwargs.keys():
            if k not in ['block', 'track']:
                raise TypeError("invalid keyword arg, %r"%k)

        assert len(sequences) > 0, "must have some sequences to map onto!"
        pf = ParallelFunction(self, f, block=block, **kwargs)
        return pf.map(*sequences)

    def execute(self, code, targets=None, block=None):
        """Executes `code` on `targets` in blocking or nonblocking manner.

        ``execute`` is always `bound` (affects engine namespace)

        Parameters
        ----------

        code : str
                the code string to be executed
        block : bool
                whether or not to wait until done to return
                default: self.block
        """
        return self._really_apply(util._execute, args=(code,), block=block, targets=targets)

    def run(self, filename, targets=None, block=None):
        """Execute contents of `filename` on my engine(s).

        This simply reads the contents of the file and calls `execute`.

        Parameters
        ----------

        filename : str
                The path to the file
        targets : int/str/list of ints/strs
                the engines on which to execute
                default : all
        block : bool
                whether or not to wait until done
                default: self.block

        """
        with open(filename, 'r') as f:
            # add newline in case of trailing indented whitespace
            # which will cause SyntaxError
            code = f.read()+'\n'
        return self.execute(code, block=block, targets=targets)

    def update(self, ns):
        """update remote namespace with dict `ns`

        See `push` for details.
        """
        return self.push(ns, block=self.block, track=self.track)

    def push(self, ns, targets=None, block=None, track=None):
        """update remote namespace with dict `ns`

        Parameters
        ----------

        ns : dict
            dict of keys with which to update engine namespace(s)
        block : bool [default : self.block]
            whether to wait to be notified of engine receipt

        """

        block = block if block is not None else self.block
        track = track if track is not None else self.track
        targets = targets if targets is not None else self.targets
        # applier = self.apply_sync if block else self.apply_async
        if not isinstance(ns, dict):
            raise TypeError("Must be a dict, not %s"%type(ns))
        return self._really_apply(util._push, (ns,), block=block, track=track, targets=targets)

    def get(self, key_s):
        """get object(s) by `key_s` from remote namespace

        see `pull` for details.
        """
        # block = block if block is not None else self.block
        return self.pull(key_s, block=True)

    def pull(self, names, targets=None, block=None):
        """get object(s) by `name` from remote namespace

        will return one object if it is a key.
        can also take a list of keys, in which case it will return a list of objects.
        """
        block = block if block is not None else self.block
        targets = targets if targets is not None else self.targets
        applier = self.apply_sync if block else self.apply_async
        if isinstance(names, basestring):
            pass
        elif isinstance(names, (list,tuple,set)):
            for key in names:
                if not isinstance(key, basestring):
                    raise TypeError("keys must be str, not type %r"%type(key))
        else:
            raise TypeError("names must be strs, not %r"%names)
        return self._really_apply(util._pull, (names,), block=block, targets=targets)

    def scatter(self, key, seq, dist='b', flatten=False, targets=None, block=None, track=None):
        """
        Partition a Python sequence and send the partitions to a set of engines.
        """
        block = block if block is not None else self.block
        track = track if track is not None else self.track
        targets = targets if targets is not None else self.targets

        mapObject = Map.dists[dist]()
        nparts = len(targets)
        msg_ids = []
        trackers = []
        for index, engineid in enumerate(targets):
            partition = mapObject.getPartition(seq, index, nparts)
            if flatten and len(partition) == 1:
                ns = {key: partition[0]}
            else:
                ns = {key: partition}
            r = self.push(ns, block=False, track=track, targets=engineid)
            msg_ids.extend(r.msg_ids)
            if track:
                trackers.append(r._tracker)

        if track:
            tracker = zmq.MessageTracker(*trackers)
        else:
            tracker = None

        r = AsyncResult(self.client, msg_ids, fname='scatter', targets=targets, tracker=tracker)
        if block:
            r.wait()
        else:
            return r

    @sync_results
    @save_ids
    def gather(self, key, dist='b', targets=None, block=None):
        """
        Gather a partitioned sequence on a set of engines as a single local seq.
        """
        block = block if block is not None else self.block
        targets = targets if targets is not None else self.targets
        mapObject = Map.dists[dist]()
        msg_ids = []

        for index, engineid in enumerate(targets):
            msg_ids.extend(self.pull(key, block=False, targets=engineid).msg_ids)

        r = AsyncMapResult(self.client, msg_ids, mapObject, fname='gather')

        if block:
            try:
                return r.get()
            except KeyboardInterrupt:
                pass
        return r

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self,key, value):
        self.update({key:value})

    def clear(self, targets=None, block=False):
        """Clear the remote namespaces on my engines."""
        block = block if block is not None else self.block
        targets = targets if targets is not None else self.targets
        return self.client.clear(targets=targets, block=block)

    def kill(self, targets=None, block=True):
        """Kill my engines."""
        block = block if block is not None else self.block
        targets = targets if targets is not None else self.targets
        return self.client.kill(targets=targets, block=block)

    #----------------------------------------
    # activate for %px,%autopx magics
    #----------------------------------------
    def activate(self):
        """Make this `View` active for parallel magic commands.

        IPython has a magic command syntax to work with `MultiEngineClient` objects.
        In a given IPython session there is a single active one.  While
        there can be many `Views` created and used by the user,
        there is only one active one.  The active `View` is used whenever
        the magic commands %px and %autopx are used.

        The activate() method is called on a given `View` to make it
        active.  Once this has been done, the magic commands can be used.
        """

        try:
            # This is injected into __builtins__.
            ip = get_ipython()
        except NameError:
            print "The IPython parallel magics (%result, %px, %autopx) only work within IPython."
        else:
            pmagic = ip.plugin_manager.get_plugin('parallelmagic')
            if pmagic is None:
                ip.magic_load_ext('parallelmagic')
                pmagic = ip.plugin_manager.get_plugin('parallelmagic')

            pmagic.active_view = self


@skip_doctest
class LoadBalancedView(View):
    """An load-balancing View that only executes via the Task scheduler.

    Load-balanced views can be created with the client's `view` method:

    >>> v = client.load_balanced_view()

    or targets can be specified, to restrict the potential destinations:

    >>> v = client.client.load_balanced_view([1,3])

    which would restrict loadbalancing to between engines 1 and 3.

    """

    follow=Any()
    after=Any()
    timeout=CFloat()
    retries = Integer(0)

    _task_scheme = Any()
    _flag_names = List(['targets', 'block', 'track', 'follow', 'after', 'timeout', 'retries'])

    def __init__(self, client=None, socket=None, **flags):
        super(LoadBalancedView, self).__init__(client=client, socket=socket, **flags)
        self._task_scheme=client._task_scheme

    def _validate_dependency(self, dep):
        """validate a dependency.

        For use in `set_flags`.
        """
        if dep is None or isinstance(dep, (basestring, AsyncResult, Dependency)):
            return True
        elif isinstance(dep, (list,set, tuple)):
            for d in dep:
                if not isinstance(d, (basestring, AsyncResult)):
                    return False
        elif isinstance(dep, dict):
            if set(dep.keys()) != set(Dependency().as_dict().keys()):
                return False
            if not isinstance(dep['msg_ids'], list):
                return False
            for d in dep['msg_ids']:
                if not isinstance(d, basestring):
                    return False
        else:
            return False

        return True

    def _render_dependency(self, dep):
        """helper for building jsonable dependencies from various input forms."""
        if isinstance(dep, Dependency):
            return dep.as_dict()
        elif isinstance(dep, AsyncResult):
            return dep.msg_ids
        elif dep is None:
            return []
        else:
            # pass to Dependency constructor
            return list(Dependency(dep))

    def set_flags(self, **kwargs):
        """set my attribute flags by keyword.

        A View is a wrapper for the Client's apply method, but with attributes
        that specify keyword arguments, those attributes can be set by keyword
        argument with this method.

        Parameters
        ----------

        block : bool
            whether to wait for results
        track : bool
            whether to create a MessageTracker to allow the user to
            safely edit after arrays and buffers during non-copying
            sends.

        after : Dependency or collection of msg_ids
            Only for load-balanced execution (targets=None)
            Specify a list of msg_ids as a time-based dependency.
            This job will only be run *after* the dependencies
            have been met.

        follow : Dependency or collection of msg_ids
            Only for load-balanced execution (targets=None)
            Specify a list of msg_ids as a location-based dependency.
            This job will only be run on an engine where this dependency
            is met.

        timeout : float/int or None
            Only for load-balanced execution (targets=None)
            Specify an amount of time (in seconds) for the scheduler to
            wait for dependencies to be met before failing with a
            DependencyTimeout.

        retries : int
            Number of times a task will be retried on failure.
        """

        super(LoadBalancedView, self).set_flags(**kwargs)
        for name in ('follow', 'after'):
            if name in kwargs:
                value = kwargs[name]
                if self._validate_dependency(value):
                    setattr(self, name, value)
                else:
                    raise ValueError("Invalid dependency: %r"%value)
        if 'timeout' in kwargs:
            t = kwargs['timeout']
            if not isinstance(t, (int, long, float, type(None))):
                raise TypeError("Invalid type for timeout: %r"%type(t))
            if t is not None:
                if t < 0:
                    raise ValueError("Invalid timeout: %s"%t)
            self.timeout = t

    @sync_results
    @save_ids
    def _really_apply(self, f, args=None, kwargs=None, block=None, track=None,
                                        after=None, follow=None, timeout=None,
                                        targets=None, retries=None):
        """calls f(*args, **kwargs) on a remote engine, returning the result.

        This method temporarily sets all of `apply`'s flags for a single call.

        Parameters
        ----------

        f : callable

        args : list [default: empty]

        kwargs : dict [default: empty]

        block : bool [default: self.block]
            whether to block
        track : bool [default: self.track]
            whether to ask zmq to track the message, for safe non-copying sends

        !!!!!! TODO: THE REST HERE  !!!!

        Returns
        -------

        if self.block is False:
            returns AsyncResult
        else:
            returns actual result of f(*args, **kwargs) on the engine(s)
            This will be a list of self.targets is also a list (even length 1), or
            the single result if self.targets is an integer engine id
        """

        # validate whether we can run
        if self._socket.closed:
            msg = "Task farming is disabled"
            if self._task_scheme == 'pure':
                msg += " because the pure ZMQ scheduler cannot handle"
                msg += " disappearing engines."
            raise RuntimeError(msg)

        if self._task_scheme == 'pure':
            # pure zmq scheme doesn't support extra features
            msg = "Pure ZMQ scheduler doesn't support the following flags:"
            "follow, after, retries, targets, timeout"
            if (follow or after or retries or targets or timeout):
                # hard fail on Scheduler flags
                raise RuntimeError(msg)
            if isinstance(f, dependent):
                # soft warn on functional dependencies
                warnings.warn(msg, RuntimeWarning)

        # build args
        args = [] if args is None else args
        kwargs = {} if kwargs is None else kwargs
        block = self.block if block is None else block
        track = self.track if track is None else track
        after = self.after if after is None else after
        retries = self.retries if retries is None else retries
        follow = self.follow if follow is None else follow
        timeout = self.timeout if timeout is None else timeout
        targets = self.targets if targets is None else targets

        if not isinstance(retries, int):
            raise TypeError('retries must be int, not %r'%type(retries))

        if targets is None:
            idents = []
        else:
            idents = self.client._build_targets(targets)[0]
            # ensure *not* bytes
            idents = [ ident.decode() for ident in idents ]

        after = self._render_dependency(after)
        follow = self._render_dependency(follow)
        subheader = dict(after=after, follow=follow, timeout=timeout, targets=idents, retries=retries)

        msg = self.client.send_apply_message(self._socket, f, args, kwargs, track=track,
                                subheader=subheader)
        tracker = None if track is False else msg['tracker']

        ar = AsyncResult(self.client, msg['header']['msg_id'], fname=f.__name__, targets=None, tracker=tracker)

        if block:
            try:
                return ar.get()
            except KeyboardInterrupt:
                pass
        return ar

    @spin_after
    @save_ids
    def map(self, f, *sequences, **kwargs):
        """view.map(f, *sequences, block=self.block, chunksize=1, ordered=True) => list|AsyncMapResult

        Parallel version of builtin `map`, load-balanced by this View.

        `block`, and `chunksize` can be specified by keyword only.

        Each `chunksize` elements will be a separate task, and will be
        load-balanced. This lets individual elements be available for iteration
        as soon as they arrive.

        Parameters
        ----------

        f : callable
            function to be mapped
        *sequences: one or more sequences of matching length
            the sequences to be distributed and passed to `f`
        block : bool [default self.block]
            whether to wait for the result or not
        track : bool
            whether to create a MessageTracker to allow the user to
            safely edit after arrays and buffers during non-copying
            sends.
        chunksize : int [default 1]
            how many elements should be in each task.
        ordered : bool [default True]
            Whether the results should be gathered as they arrive, or enforce
            the order of submission.
            
            Only applies when iterating through AsyncMapResult as results arrive.
            Has no effect when block=True.

        Returns
        -------

        if block=False:
            AsyncMapResult
                An object like AsyncResult, but which reassembles the sequence of results
                into a single list. AsyncMapResults can be iterated through before all
                results are complete.
            else:
                the result of map(f,*sequences)

        """

        # default
        block = kwargs.get('block', self.block)
        chunksize = kwargs.get('chunksize', 1)
        ordered = kwargs.get('ordered', True)

        keyset = set(kwargs.keys())
        extra_keys = keyset.difference_update(set(['block', 'chunksize']))
        if extra_keys:
            raise TypeError("Invalid kwargs: %s"%list(extra_keys))

        assert len(sequences) > 0, "must have some sequences to map onto!"

        pf = ParallelFunction(self, f, block=block, chunksize=chunksize, ordered=ordered)
        return pf.map(*sequences)

__all__ = ['LoadBalancedView', 'DirectView']
