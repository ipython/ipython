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

import os
import json
import time
import warnings
from datetime import datetime
from getpass import getpass
from pprint import pprint

pjoin = os.path.join

import zmq
# from zmq.eventloop import ioloop, zmqstream

from IPython.utils.path import get_ipython_dir
from IPython.utils.pickleutil import Reference
from IPython.utils.traitlets import (HasTraits, Int, Instance, CUnicode, 
                                    Dict, List, Bool, Str, Set)
from IPython.external.decorator import decorator
from IPython.external.ssh import tunnel

from . import error
from . import map as Map
from . import util
from . import streamsession as ss
from .asyncresult import AsyncResult, AsyncMapResult, AsyncHubResult
from .clusterdir import ClusterDir, ClusterDirError
from .dependency import Dependency, depend, require, dependent
from .remotefunction import remote, parallel, ParallelFunction, RemoteFunction
from .util import ReverseDict, validate_url, disambiguate_url
from .view import DirectView, LoadBalancedView

#--------------------------------------------------------------------------
# helpers for implementing old MEC API via client.apply
#--------------------------------------------------------------------------

def _push(user_ns, **ns):
    """helper method for implementing `client.push` via `client.apply`"""
    user_ns.update(ns)

def _pull(user_ns, keys):
    """helper method for implementing `client.pull` via `client.apply`"""
    if isinstance(keys, (list,tuple, set)):
        for key in keys:
            if not user_ns.has_key(key):
                raise NameError("name '%s' is not defined"%key)
        return map(user_ns.get, keys)
    else:
        if not user_ns.has_key(keys):
            raise NameError("name '%s' is not defined"%keys)
        return user_ns.get(keys)

def _clear(user_ns):
    """helper method for implementing `client.clear` via `client.apply`"""
    user_ns.clear()

def _execute(user_ns, code):
    """helper method for implementing `client.execute` via `client.apply`"""
    exec code in user_ns
    

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
    try:
        ret = f(self, *args, **kwargs)
    finally:
        self.block = saveblock
    return ret


#--------------------------------------------------------------------------
# Classes
#--------------------------------------------------------------------------

class Metadata(dict):
    """Subclass of dict for initializing metadata values.
    
    Attribute access works on keys.
    
    These objects have a strict set of keys - errors will raise if you try
    to add new keys.
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        md = {'msg_id' : None,
              'submitted' : None,
              'started' : None,
              'completed' : None,
              'received' : None,
              'engine_uuid' : None,
              'engine_id' : None,
              'follow' : None,
              'after' : None,
              'status' : None,

              'pyin' : None,
              'pyout' : None,
              'pyerr' : None,
              'stdout' : '',
              'stderr' : '',
            }
        self.update(md)
        self.update(dict(*args, **kwargs))
    
    def __getattr__(self, key):
        """getattr aliased to getitem"""
        if key in self.iterkeys():
            return self[key]
        else:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        """setattr aliased to setitem, with strict"""
        if key in self.iterkeys():
            self[key] = value
        else:
            raise AttributeError(key)
    
    def __setitem__(self, key, value):
        """strict static key enforcement"""
        if key in self.iterkeys():
            dict.__setitem__(self, key, value)
        else:
            raise KeyError(key)
        

class Client(HasTraits):
    """A semi-synchronous client to the IPython ZMQ controller
    
    Parameters
    ----------
    
    url_or_file : bytes; zmq url or path to ipcontroller-client.json
        Connection information for the Hub's registration.  If a json connector
        file is given, then likely no further configuration is necessary.
        [Default: use profile]
    profile : bytes
        The name of the Cluster profile to be used to find connector information.
        [Default: 'default']
    context : zmq.Context
        Pass an existing zmq.Context instance, otherwise the client will create its own.
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
    password : str 
        Your ssh password to sshserver. Note that if this is left None,
        you will be prompted for it if passwordless key based login is unavailable.
    paramiko : bool
        flag for whether to use paramiko instead of shell ssh for tunneling.
        [default: True on win32, False else]
    
    #------- exec authentication args -------
    # If even localhost is untrusted, you can have some protection against
    # unauthorized execution by using a key.  Messages are still sent
    # as cleartext, so if someone can snoop your loopback traffic this will
    # not help against malicious attacks.
    
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
    
    spin
        flushes incoming results and registration state changes
        control methods spin, and requesting `ids` also ensures up to date
    
    barrier
        wait on one or more msg_ids
    
    execution methods
        apply
        legacy: execute, run
    
    query methods
        queue_status, get_result, purge
    
    control methods
        abort, shutdown
    
    """
    
    
    block = Bool(False)
    outstanding = Set()
    results = Instance('collections.defaultdict', (dict,))
    metadata = Instance('collections.defaultdict', (Metadata,))
    history = List()
    debug = Bool(False)
    profile=CUnicode('default')
    
    _outstanding_dict = Instance('collections.defaultdict', (set,))
    _ids = List()
    _connected=Bool(False)
    _ssh=Bool(False)
    _context = Instance('zmq.Context')
    _config = Dict()
    _engines=Instance(ReverseDict, (), {})
    # _hub_socket=Instance('zmq.Socket')
    _query_socket=Instance('zmq.Socket')
    _control_socket=Instance('zmq.Socket')
    _iopub_socket=Instance('zmq.Socket')
    _notification_socket=Instance('zmq.Socket')
    _mux_socket=Instance('zmq.Socket')
    _task_socket=Instance('zmq.Socket')
    _task_scheme=Str()
    _balanced_views=Dict()
    _direct_views=Dict()
    _closed = False
    
    def __init__(self, url_or_file=None, profile='default', cluster_dir=None, ipython_dir=None,
            context=None, username=None, debug=False, exec_key=None,
            sshserver=None, sshkey=None, password=None, paramiko=None,
            ):
        super(Client, self).__init__(debug=debug, profile=profile)
        if context is None:
            context = zmq.Context()
        self._context = context
            
        
        self._setup_cluster_dir(profile, cluster_dir, ipython_dir)
        if self._cd is not None:
            if url_or_file is None:
                url_or_file = pjoin(self._cd.security_dir, 'ipcontroller-client.json')
        assert url_or_file is not None, "I can't find enough information to connect to a controller!"\
            " Please specify at least one of url_or_file or profile."
        
        try:
            validate_url(url_or_file)
        except AssertionError:
            if not os.path.exists(url_or_file):
                if self._cd:
                    url_or_file = os.path.join(self._cd.security_dir, url_or_file)
                assert os.path.exists(url_or_file), "Not a valid connection file or url: %r"%url_or_file
            with open(url_or_file) as f:
                cfg = json.loads(f.read())
        else:
            cfg = {'url':url_or_file}
        
        # sync defaults from args, json:
        if sshserver:
            cfg['ssh'] = sshserver
        if exec_key:
            cfg['exec_key'] = exec_key
        exec_key = cfg['exec_key']
        sshserver=cfg['ssh']
        url = cfg['url']
        location = cfg.setdefault('location', None)
        cfg['url'] = disambiguate_url(cfg['url'], location)
        url = cfg['url']
        
        self._config = cfg
        
        self._ssh = bool(sshserver or sshkey or password)
        if self._ssh and sshserver is None:
            # default to ssh via localhost
            sshserver = url.split('://')[1].split(':')[0]
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
        self._query_socket = self._context.socket(zmq.XREQ)
        self._query_socket.setsockopt(zmq.IDENTITY, self.session.session)
        if self._ssh:
            tunnel.tunnel_connection(self._query_socket, url, sshserver, **ssh_kwargs)
        else:
            self._query_socket.connect(url)
        
        self.session.debug = self.debug
        
        self._notification_handlers = {'registration_notification' : self._register_engine,
                                    'unregistration_notification' : self._unregister_engine,
                                    }
        self._queue_handlers = {'execute_reply' : self._handle_execute_reply,
                                'apply_reply' : self._handle_apply_reply}
        self._connect(sshserver, ssh_kwargs)
        
    def __del__(self):
        """cleanup sockets, but _not_ context."""
        self.close()
    
    def _setup_cluster_dir(self, profile, cluster_dir, ipython_dir):
        if ipython_dir is None:
            ipython_dir = get_ipython_dir()
        if cluster_dir is not None:
            try:
                self._cd = ClusterDir.find_cluster_dir(cluster_dir)
                return
            except ClusterDirError:
                pass
        elif profile is not None:
            try:
                self._cd = ClusterDir.find_cluster_dir_by_profile(
                    ipython_dir, profile)
                return
            except ClusterDirError:
                pass
        self._cd = None
    
    @property
    def ids(self):
        """Always up-to-date ids property."""
        self._flush_notifications()
        # always copy:
        return list(self._ids)
        
    def close(self):
        if self._closed:
            return
        snames = filter(lambda n: n.endswith('socket'), dir(self))
        for socket in map(lambda name: getattr(self, name), snames):
            if isinstance(socket, zmq.Socket) and not socket.closed:
                socket.close()
        self._closed = True
    
    def _update_engines(self, engines):
        """Update our engines dict and _ids from a dict of the form: {id:uuid}."""
        for k,v in engines.iteritems():
            eid = int(k)
            self._engines[eid] = bytes(v) # force not unicode
            self._ids.append(eid)
        self._ids = sorted(self._ids)
        if sorted(self._engines.keys()) != range(len(self._engines)) and \
                        self._task_scheme == 'pure' and self._task_socket:
            self._stop_scheduling_tasks()
    
    def _stop_scheduling_tasks(self):
        """Stop scheduling tasks because an engine has been unregistered
        from a pure ZMQ scheduler.
        """
        
        self._task_socket.close()
        self._task_socket = None
        msg = "An engine has been unregistered, and we are using pure " +\
              "ZMQ task scheduling.  Task farming will be disabled."
        if self.outstanding:
            msg += " If you were running tasks when this happened, " +\
                   "some `outstanding` msg_ids may never resolve."
        warnings.warn(msg, RuntimeWarning)
    
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
        
        # Maybe allow reconnecting?
        if self._connected:
            return
        self._connected=True

        def connect_socket(s, url):
            url = disambiguate_url(url, self._config['location'])
            if self._ssh:
                return tunnel.tunnel_connection(s, url, sshserver, **ssh_kwargs)
            else:
                return s.connect(url)
            
        self.session.send(self._query_socket, 'connection_request')
        idents,msg = self.session.recv(self._query_socket,mode=0)
        if self.debug:
            pprint(msg)
        msg = ss.Message(msg)
        content = msg.content
        self._config['registration'] = dict(content)
        if content.status == 'ok':
            if content.mux:
                self._mux_socket = self._context.socket(zmq.XREQ)
                self._mux_socket.setsockopt(zmq.IDENTITY, self.session.session)
                connect_socket(self._mux_socket, content.mux)
            if content.task:
                self._task_scheme, task_addr = content.task
                self._task_socket = self._context.socket(zmq.XREQ)
                self._task_socket.setsockopt(zmq.IDENTITY, self.session.session)
                connect_socket(self._task_socket, task_addr)
            if content.notification:
                self._notification_socket = self._context.socket(zmq.SUB)
                connect_socket(self._notification_socket, content.notification)
                self._notification_socket.setsockopt(zmq.SUBSCRIBE, b'')
            # if content.query:
            #     self._query_socket = self._context.socket(zmq.XREQ)
            #     self._query_socket.setsockopt(zmq.IDENTITY, self.session.session)
            #     connect_socket(self._query_socket, content.query)
            if content.control:
                self._control_socket = self._context.socket(zmq.XREQ)
                self._control_socket.setsockopt(zmq.IDENTITY, self.session.session)
                connect_socket(self._control_socket, content.control)
            if content.iopub:
                self._iopub_socket = self._context.socket(zmq.SUB)
                self._iopub_socket.setsockopt(zmq.SUBSCRIBE, b'')
                self._iopub_socket.setsockopt(zmq.IDENTITY, self.session.session)
                connect_socket(self._iopub_socket, content.iopub)
            self._update_engines(dict(content.engines))
                
        else:
            self._connected = False
            raise Exception("Failed to connect!")
    
    #--------------------------------------------------------------------------
    # handlers and callbacks for incoming messages
    #--------------------------------------------------------------------------
    
    def _unwrap_exception(self, content):
        """unwrap exception, and remap engineid to int."""
        e = error.unwrap_exception(content)
        print e.traceback
        if e.engine_info:
            e_uuid = e.engine_info['engine_uuid']
            eid = self._engines[e_uuid]
            e.engine_info['engine_id'] = eid
        return e
    
    def _extract_metadata(self, header, parent, content):
        md = {'msg_id' : parent['msg_id'],
              'received' : datetime.now(),
              'engine_uuid' : header.get('engine', None),
              'follow' : parent.get('follow', []),
              'after' : parent.get('after', []),
              'status' : content['status'],
            }
        
        if md['engine_uuid'] is not None:
            md['engine_id'] = self._engines.get(md['engine_uuid'], None)
        
        if 'date' in parent:
            md['submitted'] = datetime.strptime(parent['date'], util.ISO8601)
        if 'started' in header:
            md['started'] = datetime.strptime(header['started'], util.ISO8601)
        if 'date' in header:
            md['completed'] = datetime.strptime(header['date'], util.ISO8601)
        return md
    
    def _register_engine(self, msg):
        """Register a new engine, and update our connection info."""
        content = msg['content']
        eid = content['id']
        d = {eid : content['queue']}
        self._update_engines(d)

    def _unregister_engine(self, msg):
        """Unregister an engine that has died."""
        content = msg['content']
        eid = int(content['id'])
        if eid in self._ids:
            self._ids.remove(eid)
            uuid = self._engines.pop(eid)
            
            self._handle_stranded_msgs(eid, uuid)
                
        if self._task_socket and self._task_scheme == 'pure':
            self._stop_scheduling_tasks()
    
    def _handle_stranded_msgs(self, eid, uuid):
        """Handle messages known to be on an engine when the engine unregisters.
        
        It is possible that this will fire prematurely - that is, an engine will
        go down after completing a result, and the client will be notified
        of the unregistration and later receive the successful result.
        """
        
        outstanding = self._outstanding_dict[uuid]
        
        for msg_id in list(outstanding):
            if msg_id in self.results:
                # we already 
                continue
            try:
                raise error.EngineError("Engine %r died while running task %r"%(eid, msg_id))
            except:
                content = error.wrap_exception()
            # build a fake message:
            parent = {}
            header = {}
            parent['msg_id'] = msg_id
            header['engine'] = uuid
            header['date'] = datetime.now().strftime(util.ISO8601)
            msg = dict(parent_header=parent, header=header, content=content)
            self._handle_apply_reply(msg)
    
    def _handle_execute_reply(self, msg):
        """Save the reply to an execute_request into our results.
        
        execute messages are never actually used. apply is used instead.
        """
        
        parent = msg['parent_header']
        msg_id = parent['msg_id']
        if msg_id not in self.outstanding:
            if msg_id in self.history:
                print ("got stale result: %s"%msg_id)
            else:
                print ("got unknown result: %s"%msg_id)
        else:
            self.outstanding.remove(msg_id)
        self.results[msg_id] = self._unwrap_exception(msg['content'])
    
    def _handle_apply_reply(self, msg):
        """Save the reply to an apply_request into our results."""
        parent = msg['parent_header']
        msg_id = parent['msg_id']
        if msg_id not in self.outstanding:
            if msg_id in self.history:
                print ("got stale result: %s"%msg_id)
                print self.results[msg_id]
                print msg
            else:
                print ("got unknown result: %s"%msg_id)
        else:
            self.outstanding.remove(msg_id)
        content = msg['content']
        header = msg['header']
        
        # construct metadata:
        md = self.metadata[msg_id]
        md.update(self._extract_metadata(header, parent, content))
        # is this redundant?
        self.metadata[msg_id] = md
        
        e_outstanding = self._outstanding_dict[md['engine_uuid']]
        if msg_id in e_outstanding:
            e_outstanding.remove(msg_id)
        
        # construct result:
        if content['status'] == 'ok':
            self.results[msg_id] = util.unserialize_object(msg['buffers'])[0]
        elif content['status'] == 'aborted':
            self.results[msg_id] = error.AbortedTask(msg_id)
        elif content['status'] == 'resubmitted':
            # TODO: handle resubmission
            pass
        else:
            self.results[msg_id] = self._unwrap_exception(content)
    
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
    
    def _flush_iopub(self, sock):
        """Flush replies from the iopub channel waiting
        in the ZMQ queue.
        """
        msg = self.session.recv(sock, mode=zmq.NOBLOCK)
        while msg is not None:
            if self.debug:
                pprint(msg)
            msg = msg[-1]
            parent = msg['parent_header']
            msg_id = parent['msg_id']
            content = msg['content']
            header = msg['header']
            msg_type = msg['msg_type']
            
            # init metadata:
            md = self.metadata[msg_id]
            
            if msg_type == 'stream':
                name = content['name']
                s = md[name] or ''
                md[name] = s + content['data']
            elif msg_type == 'pyerr':
                md.update({'pyerr' : self._unwrap_exception(content)})
            else:
                md.update({msg_type : content['data']})
            
            # reduntant?
            self.metadata[msg_id] = md
            
            msg = self.session.recv(sock, mode=zmq.NOBLOCK)
    
    #--------------------------------------------------------------------------
    # len, getitem
    #--------------------------------------------------------------------------
    
    def __len__(self):
        """len(client) returns # of engines."""
        return len(self.ids)
    
    def __getitem__(self, key):
        """index access returns DirectView multiplexer objects
        
        Must be int, slice, or list/tuple/xrange of ints"""
        if not isinstance(key, (int, slice, tuple, list, xrange)):
            raise TypeError("key by int/slice/iterable of ints only, not %s"%(type(key)))
        else:
            return self.view(key, balanced=False)
    
    #--------------------------------------------------------------------------
    # Begin public methods
    #--------------------------------------------------------------------------
    
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
        if self._iopub_socket:
            self._flush_iopub(self._iopub_socket)
    
    def barrier(self, jobs=None, timeout=-1):
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
        tic = time.time()
        if jobs is None:
            theids = self.outstanding
        else:
            if isinstance(jobs, (int, str, AsyncResult)):
                jobs = [jobs]
            theids = set()
            for job in jobs:
                if isinstance(job, int):
                    # index access
                    job = self.history[job]
                elif isinstance(job, AsyncResult):
                    map(theids.add, job.msg_ids)
                    continue
                theids.add(job)
        if not theids.intersection(self.outstanding):
            return True
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
                    error = self._unwrap_exception(msg['content'])
        if error:
            raise error
        
    
    @spinfirst
    @defaultblock
    def abort(self, jobs=None, targets=None, block=None):
        """Abort specific jobs from the execution queues of target(s).
        
        This is a mechanism to prevent jobs that have already been submitted
        from executing.
        
        Parameters
        ----------
        
        jobs : msg_id, list of msg_ids, or AsyncResult
            The jobs to be aborted
        
        
        """
        targets = self._build_targets(targets)[0]
        msg_ids = []
        if isinstance(jobs, (basestring,AsyncResult)):
            jobs = [jobs]
        bad_ids = filter(lambda obj: not isinstance(obj, (basestring, AsyncResult)), jobs)
        if bad_ids:
            raise TypeError("Invalid msg_id type %r, expected str or AsyncResult"%bad_ids[0])
        for j in jobs:
            if isinstance(j, AsyncResult):
                msg_ids.extend(j.msg_ids)
            else:
                msg_ids.append(j)
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
                    error = self._unwrap_exception(msg['content'])
        if error:
            raise error
    
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
                    error = self._unwrap_exception(msg['content'])
        
        if controller:
            time.sleep(0.25)
            self.session.send(self._query_socket, 'shutdown_request')
            idents,msg = self.session.recv(self._query_socket, 0)
            if self.debug:
                pprint(msg)
            if msg['content']['status'] != 'ok':
                error = self._unwrap_exception(msg['content'])
        
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
        result = self.apply(_execute, (code,), targets=targets, block=block, bound=True, balanced=False)
        if not block:
            return result
    
    def run(self, filename, targets='all', block=None):
        """Execute contents of `filename` on engine(s). 
        
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
        return self.execute(code, targets=targets, block=block)
    
    def _maybe_raise(self, result):
        """wrapper for maybe raising an exception if apply failed."""
        if isinstance(result, error.RemoteError):
            raise result
        
        return result
    
    def _build_dependency(self, dep):
        """helper for building jsonable dependencies from various input forms"""
        if isinstance(dep, Dependency):
            return dep.as_dict()
        elif isinstance(dep, AsyncResult):
            return dep.msg_ids
        elif dep is None:
            return []
        else:
            # pass to Dependency constructor
            return list(Dependency(dep))
        
    @defaultblock
    def apply(self, f, args=None, kwargs=None, bound=False, block=None,
                        targets=None, balanced=None,
                        after=None, follow=None, timeout=None,
                        track=False):
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
        bound : bool (default: False)
            Whether to pass the Engine(s) Namespace as the first argument to `f`.
        block : bool (default: self.block)
            Whether to wait for the result, or return immediately.
            False:
                returns AsyncResult
            True:
                returns actual result(s) of f(*args, **kwargs)
                if multiple targets:
                    list of results, matching `targets`
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
        
        balanced : bool, default None
            whether to load-balance.  This will default to True
            if targets is unspecified, or False if targets is specified.
            
            The following arguments are only used when balanced is True:
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
        track : bool
            whether to track non-copying sends.
            [default False]
        
        after,follow,timeout only used if `balanced=True`.
        
        Returns
        -------
        
        if block is False:
            return AsyncResult wrapping msg_ids
            output of AsyncResult.get() is identical to that of `apply(...block=True)`
        else:
            if single target:
                return result of `f(*args, **kwargs)`
            else:
                return list of results, matching `targets`
        """
        assert not self._closed, "cannot use me anymore, I'm closed!"
        # defaults:
        block = block if block is not None else self.block
        args = args if args is not None else []
        kwargs = kwargs if kwargs is not None else {}
        
        if balanced is None:
            if targets is None:
                # default to balanced if targets unspecified
                balanced = True
            else:
                # otherwise default to multiplexing
                balanced = False
        
        if targets is None and balanced is False:
            # default to all if *not* balanced, and targets is unspecified
            targets = 'all'
        
        # enforce types of f,args,kwrags
        if not callable(f):
            raise TypeError("f must be callable, not %s"%type(f))
        if not isinstance(args, (tuple, list)):
            raise TypeError("args must be tuple or list, not %s"%type(args))
        if not isinstance(kwargs, dict):
            raise TypeError("kwargs must be dict, not %s"%type(kwargs))
        
        options  = dict(bound=bound, block=block, targets=targets, track=track)
        
        if balanced:
            return self._apply_balanced(f, args, kwargs, timeout=timeout, 
                                        after=after, follow=follow, **options)
        elif follow or after or timeout:
                msg = "follow, after, and timeout args are only used for"
                msg += " load-balanced execution."
                raise ValueError(msg)
        else:
            return self._apply_direct(f, args, kwargs, **options)
    
    def _apply_balanced(self, f, args, kwargs, bound=None, block=None, targets=None,
                            after=None, follow=None, timeout=None, track=None):
        """call f(*args, **kwargs) remotely in a load-balanced manner.
        
        This is a private method, see `apply` for details.
        Not to be called directly!
        """
        
        loc = locals()
        for name in ('bound', 'block', 'track'):
            assert loc[name] is not None, "kwarg %r must be specified!"%name
        
        if self._task_socket is None:
            msg = "Task farming is disabled"
            if self._task_scheme == 'pure':
                msg += " because the pure ZMQ scheduler cannot handle"
                msg += " disappearing engines."
            raise RuntimeError(msg)
        
        if self._task_scheme == 'pure':
            # pure zmq scheme doesn't support dependencies
            msg = "Pure ZMQ scheduler doesn't support dependencies"
            if (follow or after):
                # hard fail on DAG dependencies
                raise RuntimeError(msg)
            if isinstance(f, dependent):
                # soft warn on functional dependencies
                warnings.warn(msg, RuntimeWarning)
        
        # defaults:
        args = args if args is not None else []
        kwargs = kwargs if kwargs is not None else {}
        
        if targets:
            idents,_ = self._build_targets(targets)
        else:
            idents = []
        
        after = self._build_dependency(after)
        follow = self._build_dependency(follow)
        subheader = dict(after=after, follow=follow, timeout=timeout, targets=idents)
        bufs = util.pack_apply_message(f,args,kwargs)
        content = dict(bound=bound)
        
        msg = self.session.send(self._task_socket, "apply_request", 
                content=content, buffers=bufs, subheader=subheader, track=track)
        msg_id = msg['msg_id']
        self.outstanding.add(msg_id)
        self.history.append(msg_id)
        self.metadata[msg_id]['submitted'] = datetime.now()
        tracker = None if track is False else msg['tracker']
        ar = AsyncResult(self, [msg_id], fname=f.__name__, targets=targets, tracker=tracker)
        if block:
            try:
                return ar.get()
            except KeyboardInterrupt:
                return ar
        else:
            return ar
    
    def _apply_direct(self, f, args, kwargs, bound=None, block=None, targets=None,
                                        track=None):
        """Then underlying method for applying functions to specific engines
        via the MUX queue.
        
        This is a private method, see `apply` for details.
        Not to be called directly!
        """
        loc = locals()
        for name in ('bound', 'block', 'targets', 'track'):
            assert loc[name] is not None, "kwarg %r must be specified!"%name
        
        idents,targets = self._build_targets(targets)
        
        subheader = {}
        content = dict(bound=bound)
        bufs = util.pack_apply_message(f,args,kwargs)
        
        msg_ids = []
        trackers = []
        for ident in idents:
            msg = self.session.send(self._mux_socket, "apply_request", 
                    content=content, buffers=bufs, ident=ident, subheader=subheader,
                    track=track)
            if track:
                trackers.append(msg['tracker'])
            msg_id = msg['msg_id']
            self.outstanding.add(msg_id)
            self._outstanding_dict[ident].add(msg_id)
            self.history.append(msg_id)
            msg_ids.append(msg_id)
        
        tracker = None if track is False else zmq.MessageTracker(*trackers)
        ar = AsyncResult(self, msg_ids, fname=f.__name__, targets=targets, tracker=tracker)
        
        if block:
            try:
                return ar.get()
            except KeyboardInterrupt:
                return ar
        else:
            return ar
    
    #--------------------------------------------------------------------------
    # construct a View object
    #--------------------------------------------------------------------------
    
    @defaultblock
    def remote(self, bound=False, block=None, targets=None, balanced=None):
        """Decorator for making a RemoteFunction"""
        return remote(self, bound=bound, targets=targets, block=block, balanced=balanced)
    
    @defaultblock
    def parallel(self, dist='b', bound=False, block=None, targets=None, balanced=None):
        """Decorator for making a ParallelFunction"""
        return parallel(self, bound=bound, targets=targets, block=block, balanced=balanced)
    
    def _cache_view(self, targets, balanced):
        """save views, so subsequent requests don't create new objects."""
        if balanced:
            view_class = LoadBalancedView
            view_cache = self._balanced_views
        else:
            view_class = DirectView
            view_cache = self._direct_views
        
        # use str, since often targets will be a list
        key = str(targets)
        if key not in view_cache:
            view_cache[key] = view_class(client=self, targets=targets)
        
        return view_cache[key]
    
    def view(self, targets=None, balanced=None):
        """Method for constructing View objects.
        
        If no arguments are specified, create a LoadBalancedView
        using all engines.  If only `targets` specified, it will
        be a DirectView.  This method is the underlying implementation
        of ``client.__getitem__``.
        
        Parameters
        ----------
        
        targets: list,slice,int,etc. [default: use all engines]
            The engines to use for the View
        balanced : bool [default: False if targets specified, True else]
            whether to build a LoadBalancedView or a DirectView
        
        """
        
        balanced = (targets is None) if balanced is None else balanced
        
        if targets is None:
            if balanced:
                return self._cache_view(None,True)
            else:
                targets = slice(None)
        
        if isinstance(targets, int):
            if targets < 0:
                targets = self.ids[targets]
            if targets not in self.ids:
                raise IndexError("No such engine: %i"%targets)
            return self._cache_view(targets, balanced)
        
        if isinstance(targets, slice):
            indices = range(len(self.ids))[targets]
            ids = sorted(self._ids)
            targets = [ ids[i] for i in indices ]
        
        if isinstance(targets, (tuple, list, xrange)):
            _,targets = self._build_targets(list(targets))
            return self._cache_view(targets, balanced)
        else:
            raise TypeError("targets by int/slice/collection of ints only, not %s"%(type(targets)))
    
    #--------------------------------------------------------------------------
    # Data movement
    #--------------------------------------------------------------------------
    
    @defaultblock
    def push(self, ns, targets='all', block=None, track=False):
        """Push the contents of `ns` into the namespace on `target`"""
        if not isinstance(ns, dict):
            raise TypeError("Must be a dict, not %s"%type(ns))
        result = self.apply(_push, kwargs=ns, targets=targets, block=block, bound=True, balanced=False, track=track)
        if not block:
            return result
    
    @defaultblock
    def pull(self, keys, targets='all', block=None):
        """Pull objects from `target`'s namespace by `keys`"""
        if isinstance(keys, basestring):
            pass
        elif isinstance(keys, (list,tuple,set)):
            for key in keys:
                if not isinstance(key, basestring):
                    raise TypeError("keys must be str, not type %r"%type(key))
        else:
            raise TypeError("keys must be strs, not %r"%keys)
        result = self.apply(_pull, (keys,), targets=targets, block=block, bound=True, balanced=False)
        return result
    
    @defaultblock
    def scatter(self, key, seq, dist='b', flatten=False, targets='all', block=None, track=False):
        """
        Partition a Python sequence and send the partitions to a set of engines.
        """
        targets = self._build_targets(targets)[-1]
        mapObject = Map.dists[dist]()
        nparts = len(targets)
        msg_ids = []
        trackers = []
        for index, engineid in enumerate(targets):
            partition = mapObject.getPartition(seq, index, nparts)
            if flatten and len(partition) == 1:
                r = self.push({key: partition[0]}, targets=engineid, block=False, track=track)
            else:
                r = self.push({key: partition}, targets=engineid, block=False, track=track)
            msg_ids.extend(r.msg_ids)
            if track:
                trackers.append(r._tracker)
        
        if track:
            tracker = zmq.MessageTracker(*trackers)
        else:
            tracker = None
        
        r = AsyncResult(self, msg_ids, fname='scatter', targets=targets, tracker=tracker)
        if block:
            r.wait()
        else:
            return r
    
    @defaultblock
    def gather(self, key, dist='b', targets='all', block=None):
        """
        Gather a partitioned sequence on a set of engines as a single local seq.
        """
        
        targets = self._build_targets(targets)[-1]
        mapObject = Map.dists[dist]()
        msg_ids = []
        for index, engineid in enumerate(targets):
            msg_ids.extend(self.pull(key, targets=engineid,block=False).msg_ids)
        
        r = AsyncMapResult(self, msg_ids, mapObject, fname='gather')
        if block:
            return r.get()
        else:
            return r
    
    #--------------------------------------------------------------------------
    # Query methods
    #--------------------------------------------------------------------------
    
    @spinfirst
    @defaultblock
    def get_result(self, indices_or_msg_ids=None, block=None):
        """Retrieve a result by msg_id or history index, wrapped in an AsyncResult object.
        
        If the client already has the results, no request to the Hub will be made.
        
        This is a convenient way to construct AsyncResult objects, which are wrappers
        that include metadata about execution, and allow for awaiting results that
        were not submitted by this Client.
        
        It can also be a convenient way to retrieve the metadata associated with
        blocking execution, since it always retrieves
        
        Examples
        --------
        ::
        
            In [10]: r = client.apply()
        
        Parameters
        ----------
        
        indices_or_msg_ids : integer history index, str msg_id, or list of either
            The indices or msg_ids of indices to be retrieved
        
        block : bool
            Whether to wait for the result to be done
        
        Returns
        -------
        
        AsyncResult
            A single AsyncResult object will always be returned.
        
        AsyncHubResult
            A subclass of AsyncResult that retrieves results from the Hub
        
        """
        if indices_or_msg_ids is None:
            indices_or_msg_ids = -1
        
        if not isinstance(indices_or_msg_ids, (list,tuple)):
            indices_or_msg_ids = [indices_or_msg_ids]
        
        theids = []
        for id in indices_or_msg_ids:
            if isinstance(id, int):
                id = self.history[id]
            if not isinstance(id, str):
                raise TypeError("indices must be str or int, not %r"%id)
            theids.append(id)
        
        local_ids = filter(lambda msg_id: msg_id in self.history or msg_id in self.results, theids)
        remote_ids = filter(lambda msg_id: msg_id not in local_ids, theids)
        
        if remote_ids:
            ar = AsyncHubResult(self, msg_ids=theids)
        else:
            ar = AsyncResult(self, msg_ids=theids)
        
        if block:
            ar.wait()
        
        return ar
    
    @spinfirst
    def result_status(self, msg_ids, status_only=True):
        """Check on the status of the result(s) of the apply request with `msg_ids`.
        
        If status_only is False, then the actual results will be retrieved, else
        only the status of the results will be checked.
        
        Parameters
        ----------
        
        msg_ids : list of msg_ids
            if int:
                Passed as index to self.history for convenience.
        status_only : bool (default: True)
            if False:
                Retrieve the actual results of completed tasks.
        
        Returns
        -------
        
        results : dict
            There will always be the keys 'pending' and 'completed', which will
            be lists of msg_ids that are incomplete or complete. If `status_only`
            is False, then completed results will be keyed by their `msg_id`.
        """
        if not isinstance(msg_ids, (list,tuple)):
            msg_ids = [msg_ids]
            
        theids = []
        for msg_id in msg_ids:
            if isinstance(msg_id, int):
                msg_id = self.history[msg_id]
            if not isinstance(msg_id, basestring):
                raise TypeError("msg_ids must be str, not %r"%msg_id)
            theids.append(msg_id)
        
        completed = []
        local_results = {}
        
        # comment this block out to temporarily disable local shortcut:
        for msg_id in theids:
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
                raise self._unwrap_exception(content)
            buffers = msg['buffers']
        else:
            content = dict(completed=[],pending=[])
        
        content['completed'].extend(completed)
        
        if status_only:
            return content
        
        failures = []
        # load cached results into result:
        content.update(local_results)
        # update cache with results:
        for msg_id in sorted(theids):
            if msg_id in content['completed']:
                rec = content[msg_id]
                parent = rec['header']
                header = rec['result_header']
                rcontent = rec['result_content']
                iodict = rec['io']
                if isinstance(rcontent, str):
                    rcontent = self.session.unpack(rcontent)
                
                md = self.metadata[msg_id]
                md.update(self._extract_metadata(header, parent, rcontent))
                md.update(iodict)
                
                if rcontent['status'] == 'ok':
                    res,buffers = util.unserialize_object(buffers)
                else:
                    print rcontent
                    res = self._unwrap_exception(rcontent)
                    failures.append(res)
                
                self.results[msg_id] = res
                content[msg_id] = res
        
        if len(theids) == 1 and failures:
                raise failures[0]
        
        error.collect_exceptions(failures, "result_status")
        return content

    @spinfirst
    def queue_status(self, targets='all', verbose=False):
        """Fetch the status of engine queues.
        
        Parameters
        ----------
        
        targets : int/str/list of ints/strs
                the engines whose states are to be queried.
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
            raise self._unwrap_exception(content)
        return util.rekey(content)
        
    @spinfirst
    def purge_results(self, jobs=[], targets=[]):
        """Tell the controller to forget results.
        
        Individual results can be purged by msg_id, or the entire
        history of specific targets can be purged.
        
        Parameters
        ----------
        
        jobs : str or list of strs or AsyncResult objects
                the msg_ids whose results should be forgotten.
        targets : int/str/list of ints/strs
                The targets, by uuid or int_id, whose entire history is to be purged.
                Use `targets='all'` to scrub everything from the controller's memory.
                
                default : None
        """
        if not targets and not jobs:
            raise ValueError("Must specify at least one of `targets` and `jobs`")
        if targets:
            targets = self._build_targets(targets)[1]
        
        # construct msg_ids from jobs
        msg_ids = []
        if isinstance(jobs, (basestring,AsyncResult)):
            jobs = [jobs]
        bad_ids = filter(lambda obj: not isinstance(obj, (basestring, AsyncResult)), jobs)
        if bad_ids:
            raise TypeError("Invalid msg_id type %r, expected str or AsyncResult"%bad_ids[0])
        for j in jobs:
            if isinstance(j, AsyncResult):
                msg_ids.extend(j.msg_ids)
            else:
                msg_ids.append(j)
        
        content = dict(targets=targets, msg_ids=msg_ids)
        self.session.send(self._query_socket, "purge_request", content=content)
        idents, msg = self.session.recv(self._query_socket, 0)
        if self.debug:
            pprint(msg)
        content = msg['content']
        if content['status'] != 'ok':
            raise self._unwrap_exception(content)


__all__ = [ 'Client', 
            'depend', 
            'require', 
            'remote',
            'parallel',
            'RemoteFunction',
            'ParallelFunction',
            'DirectView',
            'LoadBalancedView',
            'AsyncResult',
            'AsyncMapResult',
            'Reference'
            ]
