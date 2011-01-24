"""A semi-synchronous Client for the ZMQ controller"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import print_function

import os
import time
from getpass import getpass
from pprint import pprint

import zmq
from zmq.eventloop import ioloop, zmqstream

from IPython.external.decorator import decorator
from IPython.zmq import tunnel

import streamsession as ss
# from remotenamespace import RemoteNamespace
from view import DirectView, LoadBalancedView
from dependency import Dependency, depend, require
import error
import map as Map

#--------------------------------------------------------------------------
# helpers for implementing old MEC API via client.apply
#--------------------------------------------------------------------------

def _push(ns):
    """helper method for implementing `client.push` via `client.apply`"""
    globals().update(ns)

def _pull(keys):
    """helper method for implementing `client.pull` via `client.apply`"""
    g = globals()
    if isinstance(keys, (list,tuple, set)):
        for key in keys:
            if not g.has_key(key):
                raise NameError("name '%s' is not defined"%key)
        return map(g.get, keys)
    else:
        if not g.has_key(keys):
            raise NameError("name '%s' is not defined"%keys)
        return g.get(keys)

def _clear():
    """helper method for implementing `client.clear` via `client.apply`"""
    globals().clear()

def execute(code):
    """helper method for implementing `client.execute` via `client.apply`"""
    exec code in globals()
    

#--------------------------------------------------------------------------
# Decorators for Client methods
#--------------------------------------------------------------------------

@decorator
def spinfirst(f, self, *args, **kwargs):
    """Call spin() to sync state prior to calling the method."""
    self.spin()
    return f(self, *args, **kwargs)

@decorator
def defaultblock(f, self, *args, **kwargs):
    """Default to self.block; preserve self.block."""
    block = kwargs.get('block',None)
    block = self.block if block is None else block
    saveblock = self.block
    self.block = block
    ret = f(self, *args, **kwargs)
    self.block = saveblock
    return ret

def remote(client, bound=False, block=None, targets=None):
    """Turn a function into a remote function.
    
    This method can be used for map:
    
    >>> @remote(client,block=True)
        def func(a)
    """
    def remote_function(f):
        return RemoteFunction(client, f, bound, block, targets)
    return remote_function

def parallel(client, dist='b', bound=False, block=None, targets='all'):
    """Turn a function into a parallel remote function.
    
    This method can be used for map:
    
    >>> @parallel(client,block=True)
        def func(a)
    """
    def parallel_function(f):
        return ParallelFunction(client, f, dist, bound, block, targets)
    return parallel_function

#--------------------------------------------------------------------------
# Classes
#--------------------------------------------------------------------------

class RemoteFunction(object):
    """Turn an existing function into a remote function.
    
    Parameters
    ----------
    
    client : Client instance
        The client to be used to connect to engines
    f : callable
        The function to be wrapped into a remote function
    bound : bool [default: False]
        Whether the affect the remote namespace when called
    block : bool [default: None]
        Whether to wait for results or not.  The default behavior is
        to use the current `block` attribute of `client`
    targets : valid target list [default: all]
        The targets on which to execute.
    """
    
    client = None # the remote connection
    func = None # the wrapped function
    block = None # whether to block
    bound = None # whether to affect the namespace
    targets = None # where to execute
    
    def __init__(self, client, f, bound=False, block=None, targets=None):
        self.client = client
        self.func = f
        self.block=block
        self.bound=bound
        self.targets=targets
    
    def __call__(self, *args, **kwargs):
        return self.client.apply(self.func, args=args, kwargs=kwargs,
                block=self.block, targets=self.targets, bound=self.bound)
    

class ParallelFunction(RemoteFunction):
    """Class for mapping a function to sequences."""
    def __init__(self, client, f, dist='b', bound=False, block=None, targets='all'):
        super(ParallelFunction, self).__init__(client,f,bound,block,targets)
        mapClass = Map.dists[dist]
        self.mapObject = mapClass()
    
    def __call__(self, *sequences):
        len_0 = len(sequences[0])
        for s in sequences:
            if len(s)!=len_0:
                raise ValueError('all sequences must have equal length')
        
        if self.targets is None:
            # load-balanced:
            engines = [None]*len_0
        else:
            # multiplexed:
            engines = self.client._build_targets(self.targets)[-1]
        
        nparts = len(engines)
        msg_ids = []
        for index, engineid in enumerate(engines):
            args = []
            for seq in sequences:
                args.append(self.mapObject.getPartition(seq, index, nparts))
            mid = self.client.apply(self.func, args=args, block=False, 
                        bound=self.bound,
                        targets=engineid)
            msg_ids.append(mid)
        
        if self.block:
            dg = PendingMapResult(self.client, msg_ids, self.mapObject)
            dg.wait()
            return dg.result
        else:
            return dg
        

class PendingResult(object):
    """Class for representing results of non-blocking calls."""
    def __init__(self, client, msg_ids):
        self.client = client
        self.msg_ids = msg_ids
        self._result = None
        self.done = False
    
    def __repr__(self):
        if self.done:
            return "<%s: finished>"%(self.__class__.__name__)
        else:
            return "<%s: %r>"%(self.__class__.__name__,self.msg_ids)
    
    @property
    def result(self):
        if self._result is not None:
            return self._result
        if not self.done:
            self.wait(0)
        if self.done:
            results = map(self.client.results.get, self.msg_ids)
            results = error.collect_exceptions(results, 'get_result')
            self._result = self.reconstruct_result(results)
            return self._result
        else:
            raise error.ResultNotCompleted
    
    def reconstruct_result(self, res):
        """
        Override me in subclasses for turning a list of results
        into the expected form.
        """
        if len(res) == 1:
            return res[0]
        else:
            return res
    
    def wait(self, timout=-1):
        self.done = self.client.barrier(self.msg_ids)
        return self.done

class PendingMapResult(PendingResult):
    """Class for representing results of non-blocking gathers.
    
    This will properly reconstruct the gather.
    """
    
    def __init__(self, client, msg_ids, mapObject):
        self.mapObject = mapObject
        PendingResult.__init__(self, client, msg_ids)
    
    def reconstruct_result(self, res):
        """Perform the gather on the actual results."""
        return self.mapObject.joinPartitions(res)
    
        

class AbortedTask(object):
    """A basic wrapper object describing an aborted task."""
    def __init__(self, msg_id):
        self.msg_id = msg_id

class ResultDict(dict):
    """A subclass of dict that raises errors if it has them."""
    def __getitem__(self, key):
        res = dict.__getitem__(self, key)
        if isinstance(res, error.KernelError):
            raise res
        return res

class Client(object):
    """A semi-synchronous client to the IPython ZMQ controller
    
    Parameters
    ----------
    
    addr : bytes; zmq url, e.g. 'tcp://127.0.0.1:10101'
        The address of the controller's registration socket.
        [Default: 'tcp://127.0.0.1:10101']
    context : zmq.Context
        Pass an existing zmq.Context instance, otherwise the client will create its own
    username : bytes
        set username to be passed to the Session object
    debug : bool
        flag for lots of message printing for debug purposes
 
    #-------------- ssh related args ----------------
    # These are args for configuring the ssh tunnel to be used
    # credentials are used to forward connections over ssh to the Controller
    # Note that the ip given in `addr` needs to be relative to sshserver
    # The most basic case is to leave addr as pointing to localhost (127.0.0.1),
    # and set sshserver as the same machine the Controller is on. However, 
    # the only requirement is that sshserver is able to see the Controller
    # (i.e. is within the same trusted network).
    
    sshserver : str
        A string of the form passed to ssh, i.e. 'server.tld' or 'user@server.tld:port'
        If keyfile or password is specified, and this is not, it will default to
        the ip given in addr.
    sshkey : str; path to public ssh key file
        This specifies a key to be used in ssh login, default None.
        Regular default ssh keys will be used without specifying this argument.
    password : str; 
        Your ssh password to sshserver. Note that if this is left None,
        you will be prompted for it if passwordless key based login is unavailable.
    
    #------- exec authentication args -------
    # If even localhost is untrusted, you can have some protection against
    # unauthorized execution by using a key.  Messages are still sent
    # as cleartext, so if someone can snoop your loopback traffic this will
    # not help anything.
    
    exec_key : str
        an authentication key or file containing a key
        default: None
    
    
    Attributes
    ----------
    ids : set of int engine IDs
        requesting the ids attribute always synchronizes
        the registration state. To request ids without synchronization,
        use semi-private _ids attributes.
    
    history : list of msg_ids
        a list of msg_ids, keeping track of all the execution
        messages you have submitted in order.
    
    outstanding : set of msg_ids
        a set of msg_ids that have been submitted, but whose
        results have not yet been received.
    
    results : dict
        a dict of all our results, keyed by msg_id
    
    block : bool
        determines default behavior when block not specified
        in execution methods
    
    Methods
    -------
    spin : flushes incoming results and registration state changes
            control methods spin, and requesting `ids` also ensures up to date
            
    barrier : wait on one or more msg_ids
    
    execution methods: apply/apply_bound/apply_to/apply_bound
        legacy: execute, run
    
    query methods: queue_status, get_result, purge
    
    control methods: abort, kill
    
    """
    
    
    _connected=False
    _ssh=False
    _engines=None
    _addr='tcp://127.0.0.1:10101'
    _registration_socket=None
    _query_socket=None
    _control_socket=None
    _notification_socket=None
    _mux_socket=None
    _task_socket=None
    block = False
    outstanding=None
    results = None
    history = None
    debug = False
    
    def __init__(self, addr='tcp://127.0.0.1:10101', context=None, username=None, debug=False, 
            sshserver=None, sshkey=None, password=None, paramiko=None,
            exec_key=None,):
        if context is None:
            context = zmq.Context()
        self.context = context
        self._addr = addr
        self._ssh = bool(sshserver or sshkey or password)
        if self._ssh and sshserver is None:
            # default to the same
            sshserver = addr.split('://')[1].split(':')[0]
        if self._ssh and password is None:
            if tunnel.try_passwordless_ssh(sshserver, sshkey, paramiko):
                password=False
            else:
                password = getpass("SSH Password for %s: "%sshserver)
        ssh_kwargs = dict(keyfile=sshkey, password=password, paramiko=paramiko)
        
        if exec_key is not None and os.path.isfile(exec_key):
            arg = 'keyfile'
        else:
            arg = 'key'
        key_arg = {arg:exec_key}
        if username is None:
            self.session = ss.StreamSession(**key_arg)
        else:
            self.session = ss.StreamSession(username, **key_arg)
        self._registration_socket = self.context.socket(zmq.XREQ)
        self._registration_socket.setsockopt(zmq.IDENTITY, self.session.session)
        if self._ssh:
            tunnel.tunnel_connection(self._registration_socket, addr, sshserver, **ssh_kwargs)
        else:
            self._registration_socket.connect(addr)
        self._engines = {}
        self._ids = set()
        self.outstanding=set()
        self.results = {}
        self.history = []
        self.debug = debug
        self.session.debug = debug
        
        self._notification_handlers = {'registration_notification' : self._register_engine,
                                    'unregistration_notification' : self._unregister_engine,
                                    }
        self._queue_handlers = {'execute_reply' : self._handle_execute_reply,
                                'apply_reply' : self._handle_apply_reply}
        self._connect(sshserver, ssh_kwargs)
        
    
    @property
    def ids(self):
        """Always up to date ids property."""
        self._flush_notifications()
        return self._ids
    
    def _update_engines(self, engines):
        """Update our engines dict and _ids from a dict of the form: {id:uuid}."""
        for k,v in engines.iteritems():
            eid = int(k)
            self._engines[eid] = bytes(v) # force not unicode
            self._ids.add(eid)
    
    def _build_targets(self, targets):
        """Turn valid target IDs or 'all' into two lists:
        (int_ids, uuids).
        """
        if targets is None:
            targets = self._ids
        elif isinstance(targets, str):
            if targets.lower() == 'all':
                targets = self._ids
            else:
                raise TypeError("%r not valid str target, must be 'all'"%(targets))
        elif isinstance(targets, int):
            targets = [targets]
        return [self._engines[t] for t in targets], list(targets)
    
    def _connect(self, sshserver, ssh_kwargs):
        """setup all our socket connections to the controller. This is called from
        __init__."""
        if self._connected:
            return
        self._connected=True

        def connect_socket(s, addr):
            if self._ssh:
                return tunnel.tunnel_connection(s, addr, sshserver, **ssh_kwargs)
            else:
                return s.connect(addr)
            
        self.session.send(self._registration_socket, 'connection_request')
        idents,msg = self.session.recv(self._registration_socket,mode=0)
        if self.debug:
            pprint(msg)
        msg = ss.Message(msg)
        content = msg.content
        if content.status == 'ok':
            if content.queue:
                self._mux_socket = self.context.socket(zmq.PAIR)
                self._mux_socket.setsockopt(zmq.IDENTITY, self.session.session)
                connect_socket(self._mux_socket, content.queue)
            if content.task:
                self._task_socket = self.context.socket(zmq.PAIR)
                self._task_socket.setsockopt(zmq.IDENTITY, self.session.session)
                connect_socket(self._task_socket, content.task)
            if content.notification:
                self._notification_socket = self.context.socket(zmq.SUB)
                connect_socket(self._notification_socket, content.notification)
                self._notification_socket.setsockopt(zmq.SUBSCRIBE, "")
            if content.query:
                self._query_socket = self.context.socket(zmq.PAIR)
                self._query_socket.setsockopt(zmq.IDENTITY, self.session.session)
                connect_socket(self._query_socket, content.query)
            if content.control:
                self._control_socket = self.context.socket(zmq.PAIR)
                self._control_socket.setsockopt(zmq.IDENTITY, self.session.session)
                connect_socket(self._control_socket, content.control)
            self._update_engines(dict(content.engines))
                
        else:
            self._connected = False
            raise Exception("Failed to connect!")
    
    #--------------------------------------------------------------------------
    # handlers and callbacks for incoming messages
    #--------------------------------------------------------------------------
    
    def _register_engine(self, msg):
        """Register a new engine, and update our connection info."""
        content = msg['content']
        eid = content['id']
        d = {eid : content['queue']}
        self._update_engines(d)
        self._ids.add(int(eid))

    def _unregister_engine(self, msg):
        """Unregister an engine that has died."""
        content = msg['content']
        eid = int(content['id'])
        if eid in self._ids:
            self._ids.remove(eid)
            self._engines.pop(eid)
        
    def _handle_execute_reply(self, msg):
        """Save the reply to an execute_request into our results."""
        parent = msg['parent_header']
        msg_id = parent['msg_id']
        if msg_id not in self.outstanding:
            print("got unknown result: %s"%msg_id)
        else:
            self.outstanding.remove(msg_id)
        self.results[msg_id] = ss.unwrap_exception(msg['content'])
    
    def _handle_apply_reply(self, msg):
        """Save the reply to an apply_request into our results."""
        parent = msg['parent_header']
        msg_id = parent['msg_id']
        if msg_id not in self.outstanding:
            print ("got unknown result: %s"%msg_id)
        else:
            self.outstanding.remove(msg_id)
        content = msg['content']
        if content['status'] == 'ok':
            self.results[msg_id] = ss.unserialize_object(msg['buffers'])
        elif content['status'] == 'aborted':
            self.results[msg_id] = error.AbortedTask(msg_id)
        elif content['status'] == 'resubmitted':
            # TODO: handle resubmission
            pass
        else:
            e = ss.unwrap_exception(content)
            e_uuid = e.engine_info['engineid']
            for k,v in self._engines.iteritems():
                if v == e_uuid:
                    e.engine_info['engineid'] = k
                    break
            self.results[msg_id] = e
    
    def _flush_notifications(self):
        """Flush notifications of engine registrations waiting
        in ZMQ queue."""
        msg = self.session.recv(self._notification_socket, mode=zmq.NOBLOCK)
        while msg is not None:
            if self.debug:
                pprint(msg)
            msg = msg[-1]
            msg_type = msg['msg_type']
            handler = self._notification_handlers.get(msg_type, None)
            if handler is None:
                raise Exception("Unhandled message type: %s"%msg.msg_type)
            else:
                handler(msg)
            msg = self.session.recv(self._notification_socket, mode=zmq.NOBLOCK)
    
    def _flush_results(self, sock):
        """Flush task or queue results waiting in ZMQ queue."""
        msg = self.session.recv(sock, mode=zmq.NOBLOCK)
        while msg is not None:
            if self.debug:
                pprint(msg)
            msg = msg[-1]
            msg_type = msg['msg_type']
            handler = self._queue_handlers.get(msg_type, None)
            if handler is None:
                raise Exception("Unhandled message type: %s"%msg.msg_type)
            else:
                handler(msg)
            msg = self.session.recv(sock, mode=zmq.NOBLOCK)
    
    def _flush_control(self, sock):
        """Flush replies from the control channel waiting
        in the ZMQ queue.
        
        Currently: ignore them."""
        msg = self.session.recv(sock, mode=zmq.NOBLOCK)
        while msg is not None:
            if self.debug:
                pprint(msg)
            msg = self.session.recv(sock, mode=zmq.NOBLOCK)
    
    #--------------------------------------------------------------------------
    # getitem
    #--------------------------------------------------------------------------
    
    def __getitem__(self, key):
        """Dict access returns DirectView multiplexer objects or,
        if key is None, a LoadBalancedView."""
        if key is None:
            return LoadBalancedView(self)
        if isinstance(key, int):
            if key not in self.ids:
                raise IndexError("No such engine: %i"%key)
            return DirectView(self, key)
        
        if isinstance(key, slice):
            indices = range(len(self.ids))[key]
            ids = sorted(self._ids)
            key = [ ids[i] for i in indices ]
            # newkeys = sorted(self._ids)[thekeys[k]]
        
        if isinstance(key, (tuple, list, xrange)):
            _,targets = self._build_targets(list(key))
            return DirectView(self, targets)
        else:
            raise TypeError("key by int/iterable of ints only, not %s"%(type(key)))
    
    #--------------------------------------------------------------------------
    # Begin public methods
    #--------------------------------------------------------------------------
    
    @property
    def remote(self):
        """property for convenient RemoteFunction generation.
        
        >>> @client.remote
        ... def f():
                import os
                print (os.getpid())
        """
        return remote(self, block=self.block)
    
    def spin(self):
        """Flush any registration notifications and execution results
        waiting in the ZMQ queue.
        """
        if self._notification_socket:
            self._flush_notifications()
        if self._mux_socket:
            self._flush_results(self._mux_socket)
        if self._task_socket:
            self._flush_results(self._task_socket)
        if self._control_socket:
            self._flush_control(self._control_socket)
    
    def barrier(self, msg_ids=None, timeout=-1):
        """waits on one or more `msg_ids`, for up to `timeout` seconds.
        
        Parameters
        ----------
        msg_ids : int, str, or list of ints and/or strs
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
        tic = time.time()
        if msg_ids is None:
            theids = self.outstanding
        else:
            if isinstance(msg_ids, (int, str)):
                msg_ids = [msg_ids]
            theids = set()
            for msg_id in msg_ids:
                if isinstance(msg_id, int):
                    msg_id = self.history[msg_id]
                theids.add(msg_id)
        self.spin()
        while theids.intersection(self.outstanding):
            if timeout >= 0 and ( time.time()-tic ) > timeout:
                break
            time.sleep(1e-3)
            self.spin()
        return len(theids.intersection(self.outstanding)) == 0
    
    #--------------------------------------------------------------------------
    # Control methods
    #--------------------------------------------------------------------------
    
    @spinfirst
    @defaultblock
    def clear(self, targets=None, block=None):
        """Clear the namespace in target(s)."""
        targets = self._build_targets(targets)[0]
        for t in targets:
            self.session.send(self._control_socket, 'clear_request', content={}, ident=t)
        error = False
        if self.block:
            for i in range(len(targets)):
                idents,msg = self.session.recv(self._control_socket,0)
                if self.debug:
                    pprint(msg)
                if msg['content']['status'] != 'ok':
                    error = ss.unwrap_exception(msg['content'])
        if error:
            return error
        
    
    @spinfirst
    @defaultblock
    def abort(self, msg_ids = None, targets=None, block=None):
        """Abort the execution queues of target(s)."""
        targets = self._build_targets(targets)[0]
        if isinstance(msg_ids, basestring):
            msg_ids = [msg_ids]
        content = dict(msg_ids=msg_ids)
        for t in targets:
            self.session.send(self._control_socket, 'abort_request', 
                    content=content, ident=t)
        error = False
        if self.block:
            for i in range(len(targets)):
                idents,msg = self.session.recv(self._control_socket,0)
                if self.debug:
                    pprint(msg)
                if msg['content']['status'] != 'ok':
                    error = ss.unwrap_exception(msg['content'])
        if error:
            return error
    
    @spinfirst
    @defaultblock
    def shutdown(self, targets=None, restart=False, controller=False, block=None):
        """Terminates one or more engine processes, optionally including the controller."""
        if controller:
            targets = 'all'
        targets = self._build_targets(targets)[0]
        for t in targets:
            self.session.send(self._control_socket, 'shutdown_request', 
                        content={'restart':restart},ident=t)
        error = False
        if block or controller:
            for i in range(len(targets)):
                idents,msg = self.session.recv(self._control_socket,0)
                if self.debug:
                    pprint(msg)
                if msg['content']['status'] != 'ok':
                    error = ss.unwrap_exception(msg['content'])
        
        if controller:
            time.sleep(0.25)
            self.session.send(self._query_socket, 'shutdown_request')
            idents,msg = self.session.recv(self._query_socket, 0)
            if self.debug:
                pprint(msg)
            if msg['content']['status'] != 'ok':
                error = ss.unwrap_exception(msg['content'])
        
        if error:
            raise error
    
    #--------------------------------------------------------------------------
    # Execution methods
    #--------------------------------------------------------------------------
    
    @defaultblock
    def execute(self, code, targets='all', block=None):
        """Executes `code` on `targets` in blocking or nonblocking manner.
        
        ``execute`` is always `bound` (affects engine namespace)
        
        Parameters
        ----------
        code : str
                the code string to be executed
        targets : int/str/list of ints/strs
                the engines on which to execute
                default : all
        block : bool
                whether or not to wait until done to return
                default: self.block
        """
        result = self.apply(execute, (code,), targets=targets, block=block, bound=True)
        return result
    
    def run(self, code, block=None):
        """Runs `code` on an engine. 
        
        Calls to this are load-balanced.
        
        ``run`` is never `bound` (no effect on engine namespace)
        
        Parameters
        ----------
        code : str
                the code string to be executed
        block : bool
                whether or not to wait until done
        
        """
        result = self.apply(execute, (code,), targets=None, block=block, bound=False)
        return result
    
    def _maybe_raise(self, result):
        """wrapper for maybe raising an exception if apply failed."""
        if isinstance(result, error.RemoteError):
            raise result
        
        return result
            
    def apply(self, f, args=None, kwargs=None, bound=True, block=None, targets=None,
                        after=None, follow=None):
        """Call `f(*args, **kwargs)` on a remote engine(s), returning the result.
        
        This is the central execution command for the client.
        
        Parameters
        ----------
        
        f : function
            The fuction to be called remotely
        args : tuple/list
            The positional arguments passed to `f`
        kwargs : dict
            The keyword arguments passed to `f`
        bound : bool (default: True)
            Whether to execute in the Engine(s) namespace, or in a clean
            namespace not affecting the engine.
        block : bool (default: self.block)
            Whether to wait for the result, or return immediately.
            False:
                returns msg_id(s)
                if multiple targets:
                    list of ids
            True:
                returns actual result(s) of f(*args, **kwargs)
                if multiple targets:
                    dict of results, by engine ID
        targets : int,list of ints, 'all', None
            Specify the destination of the job.
            if None:
                Submit via Task queue for load-balancing.
            if 'all':
                Run on all active engines
            if list:
                Run on each specified engine
            if int:
                Run on single engine
            
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
        
        Returns
        -------
        if block is False:
            if single target:
                return msg_id
            else:
                return list of msg_ids
                ? (should this be dict like block=True) ?
        else:
            if single target:
                return result of f(*args, **kwargs)
            else:
                return dict of results, keyed by engine
        """
        
        # defaults:
        block = block if block is not None else self.block
        args = args if args is not None else []
        kwargs = kwargs if kwargs is not None else {}
        
        # enforce types of f,args,kwrags
        if not callable(f):
            raise TypeError("f must be callable, not %s"%type(f))
        if not isinstance(args, (tuple, list)):
            raise TypeError("args must be tuple or list, not %s"%type(args))
        if not isinstance(kwargs, dict):
            raise TypeError("kwargs must be dict, not %s"%type(kwargs))
            
        options  = dict(bound=bound, block=block, after=after, follow=follow)
            
        if targets is None:
            return self._apply_balanced(f, args, kwargs, **options)
        else:
            return self._apply_direct(f, args, kwargs, targets=targets, **options)
    
    def _apply_balanced(self, f, args, kwargs, bound=True, block=None,
                            after=None, follow=None):
        """The underlying method for applying functions in a load balanced
        manner, via the task queue."""
        if isinstance(after, Dependency):
            after = after.as_dict()
        elif after is None:
            after = []
        if isinstance(follow, Dependency):
            follow = follow.as_dict()
        elif follow is None:
            follow = []
        subheader = dict(after=after, follow=follow)
        
        bufs = ss.pack_apply_message(f,args,kwargs)
        content = dict(bound=bound)
        msg = self.session.send(self._task_socket, "apply_request", 
                content=content, buffers=bufs, subheader=subheader)
        msg_id = msg['msg_id']
        self.outstanding.add(msg_id)
        self.history.append(msg_id)
        if block:
            self.barrier(msg_id)
            return self._maybe_raise(self.results[msg_id])
        else:
            return PendingResult(self, [msg_id])
    
    def _apply_direct(self, f, args, kwargs, bound=True, block=None, targets=None,
                                after=None, follow=None):
        """Then underlying method for applying functions to specific engines
        via the MUX queue."""
        
        queues,targets = self._build_targets(targets)
        bufs = ss.pack_apply_message(f,args,kwargs)
        if isinstance(after, Dependency):
            after = after.as_dict()
        elif after is None:
            after = []
        if isinstance(follow, Dependency):
            follow = follow.as_dict()
        elif follow is None:
            follow = []
        subheader = dict(after=after, follow=follow)
        content = dict(bound=bound)
        msg_ids = []
        for queue in queues:
            msg = self.session.send(self._mux_socket, "apply_request", 
                    content=content, buffers=bufs,ident=queue, subheader=subheader)
            msg_id = msg['msg_id']
            self.outstanding.add(msg_id)
            self.history.append(msg_id)
            msg_ids.append(msg_id)
        if block:
            self.barrier(msg_ids)
        else:
            return PendingResult(self, msg_ids)
        if len(msg_ids) == 1:
            return self._maybe_raise(self.results[msg_ids[0]])
        else:
            result = {}
            for target,mid in zip(targets, msg_ids):
                    result[target] = self.results[mid]
            return error.collect_exceptions(result, f.__name__)
    
    @defaultblock
    def map(self, f, sequences, targets=None, block=None, bound=False):
        pf = ParallelFunction(self,f,block=block,bound=bound,targets=targets)
        return pf(*sequences)
    
    #--------------------------------------------------------------------------
    # Data movement
    #--------------------------------------------------------------------------
    
    @defaultblock
    def push(self, ns, targets='all', block=None):
        """Push the contents of `ns` into the namespace on `target`"""
        if not isinstance(ns, dict):
            raise TypeError("Must be a dict, not %s"%type(ns))
        result = self.apply(_push, (ns,), targets=targets, block=block, bound=True)
        return result
    
    @defaultblock
    def pull(self, keys, targets='all', block=True):
        """Pull objects from `target`'s namespace by `keys`"""
        if isinstance(keys, str):
            pass
        elif isinstance(keys, (list,tuple,set)):
            for key in keys:
                if not isinstance(key, str):
                    raise TypeError
        result = self.apply(_pull, (keys,), targets=targets, block=block, bound=True)
        return result
    
    @defaultblock
    def scatter(self, key, seq, dist='b', flatten=False, targets='all', block=None):
        """
        Partition a Python sequence and send the partitions to a set of engines.
        """
        targets = self._build_targets(targets)[-1]
        mapObject = Map.dists[dist]()
        nparts = len(targets)
        msg_ids = []
        for index, engineid in enumerate(targets):
            partition = mapObject.getPartition(seq, index, nparts)
            if flatten and len(partition) == 1:
                mid = self.push({key: partition[0]}, targets=engineid, block=False)
            else:
                mid = self.push({key: partition}, targets=engineid, block=False)
            msg_ids.append(mid)
        r = PendingResult(self, msg_ids)
        if block:
            r.wait()
            return
        else:
            return r
    
    @defaultblock
    def gather(self, key, dist='b', targets='all', block=True):
        """
        Gather a partitioned sequence on a set of engines as a single local seq.
        """
        
        targets = self._build_targets(targets)[-1]
        mapObject = Map.dists[dist]()
        msg_ids = []
        for index, engineid in enumerate(targets):
            msg_ids.append(self.pull(key, targets=engineid,block=False))
        
        r = PendingMapResult(self, msg_ids, mapObject)
        if block:
            r.wait()
            return r.result
        else:
            return r
    
    #--------------------------------------------------------------------------
    # Query methods
    #--------------------------------------------------------------------------
    
    @spinfirst
    def get_results(self, msg_ids, status_only=False):
        """Returns the result of the execute or task request with `msg_ids`.
        
        Parameters
        ----------
        msg_ids : list of ints or msg_ids
            if int:
                Passed as index to self.history for convenience.
        status_only : bool (default: False)
            if False:
                return the actual results
        """
        if not isinstance(msg_ids, (list,tuple)):
            msg_ids = [msg_ids]
        theids = []
        for msg_id in msg_ids:
            if isinstance(msg_id, int):
                msg_id = self.history[msg_id]
            if not isinstance(msg_id, str):
                raise TypeError("msg_ids must be str, not %r"%msg_id)
            theids.append(msg_id)
        
        completed = []
        local_results = {}
        for msg_id in list(theids):
            if msg_id in self.results:
                completed.append(msg_id)
                local_results[msg_id] = self.results[msg_id]
                theids.remove(msg_id)
        
        if theids: # some not locally cached
            content = dict(msg_ids=theids, status_only=status_only)
            msg = self.session.send(self._query_socket, "result_request", content=content)
            zmq.select([self._query_socket], [], [])
            idents,msg = self.session.recv(self._query_socket, zmq.NOBLOCK)
            if self.debug:
                pprint(msg)
            content = msg['content']
            if content['status'] != 'ok':
                raise ss.unwrap_exception(content)
        else:
            content = dict(completed=[],pending=[])
        if not status_only:
            # load cached results into result:
            content['completed'].extend(completed)
            content.update(local_results)
            # update cache with results:
            for msg_id in msg_ids:
                if msg_id in content['completed']:
                    self.results[msg_id] = content[msg_id]
        return content

    @spinfirst
    def queue_status(self, targets=None, verbose=False):
        """Fetch the status of engine queues.
        
        Parameters
        ----------
        targets : int/str/list of ints/strs
                the engines on which to execute
                default : all
        verbose : bool
                Whether to return lengths only, or lists of ids for each element
        """
        targets = self._build_targets(targets)[1]
        content = dict(targets=targets, verbose=verbose)
        self.session.send(self._query_socket, "queue_request", content=content)
        idents,msg = self.session.recv(self._query_socket, 0)
        if self.debug:
            pprint(msg)
        content = msg['content']
        status = content.pop('status')
        if status != 'ok':
            raise ss.unwrap_exception(content)
        return content
        
    @spinfirst
    def purge_results(self, msg_ids=[], targets=[]):
        """Tell the controller to forget results.
        
        Individual results can be purged by msg_id, or the entire
        history of specific targets can be purged.
        
        Parameters
        ----------
        msg_ids : str or list of strs
                the msg_ids whose results should be forgotten.
        targets : int/str/list of ints/strs
                The targets, by uuid or int_id, whose entire history is to be purged.
                Use `targets='all'` to scrub everything from the controller's memory.
                
                default : None
        """
        if not targets and not msg_ids:
            raise ValueError
        if targets:
            targets = self._build_targets(targets)[1]
        content = dict(targets=targets, msg_ids=msg_ids)
        self.session.send(self._query_socket, "purge_request", content=content)
        idents, msg = self.session.recv(self._query_socket, 0)
        if self.debug:
            pprint(msg)
        content = msg['content']
        if content['status'] != 'ok':
            raise ss.unwrap_exception(content)

class AsynClient(Client):
    """An Asynchronous client, using the Tornado Event Loop.
    !!!unfinished!!!"""
    io_loop = None
    _queue_stream = None
    _notifier_stream = None
    _task_stream = None
    _control_stream = None
    
    def __init__(self, addr, context=None, username=None, debug=False, io_loop=None):
        Client.__init__(self, addr, context, username, debug)
        if io_loop is None:
            io_loop = ioloop.IOLoop.instance()
        self.io_loop = io_loop
        
        self._queue_stream = zmqstream.ZMQStream(self._mux_socket, io_loop)
        self._control_stream = zmqstream.ZMQStream(self._control_socket, io_loop)
        self._task_stream = zmqstream.ZMQStream(self._task_socket, io_loop)
        self._notification_stream = zmqstream.ZMQStream(self._notification_socket, io_loop)
    
    def spin(self):
        for stream in (self.queue_stream, self.notifier_stream, 
                        self.task_stream, self.control_stream):
            stream.flush()

__all__ = [ 'Client', 
            'depend', 
            'require', 
            'remote',
            'parallel',
            'RemoteFunction',
            'ParallelFunction',
            'DirectView',
            'LoadBalancedView',
            'PendingResult',
            'PendingMapResult'
            ]
