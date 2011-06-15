"""A semi-synchronous Client for the ZMQ cluster

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
from IPython.utils.traitlets import (HasTraits, Int, Instance, Unicode,
                                    Dict, List, Bool, Set)
from IPython.external.decorator import decorator
from IPython.external.ssh import tunnel

from IPython.parallel import error
from IPython.parallel import util

from IPython.zmq.session import Session, Message

from .asyncresult import AsyncResult, AsyncHubResult
from IPython.core.application import ProfileDir, ProfileDirError
from .view import DirectView, LoadBalancedView

#--------------------------------------------------------------------------
# Decorators for Client methods
#--------------------------------------------------------------------------

@decorator
def spin_first(f, self, *args, **kwargs):
    """Call spin() to sync state prior to calling the method."""
    self.spin()
    return f(self, *args, **kwargs)


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
    """A semi-synchronous client to the IPython ZMQ cluster
    
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
    debug : bool
        flag for lots of message printing for debug purposes
    timeout : int/float 
        time (in seconds) to wait for connection replies from the Hub
        [Default: 10]
 
    #-------------- session related args ----------------
    
    config : Config object
        If specified, this will be relayed to the Session for configuration
    username : str
        set username for the session object
    packer : str (import_string) or callable
        Can be either the simple keyword 'json' or 'pickle', or an import_string to a
        function to serialize messages. Must support same input as
        JSON, and output must be bytes.
        You can pass a callable directly as `pack`
    unpacker : str (import_string) or callable
        The inverse of packer.  Only necessary if packer is specified as *not* one
        of 'json' or 'pickle'.
    
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
    
    ------- exec authentication args -------
    If even localhost is untrusted, you can have some protection against
    unauthorized execution by signing messages with HMAC digests.  
    Messages are still sent as cleartext, so if someone can snoop your 
    loopback traffic this will not protect your privacy, but will prevent
    unauthorized execution.
    
    exec_key : str
        an authentication key or file containing a key
        default: None
    
    
    Attributes
    ----------
    
    ids : list of int engine IDs
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
    
    wait
        wait on one or more msg_ids
    
    execution methods
        apply
        legacy: execute, run
    
    data movement
        push, pull, scatter, gather
    
    query methods
        queue_status, get_result, purge, result_status
    
    control methods
        abort, shutdown
    
    """
    
    
    block = Bool(False)
    outstanding = Set()
    results = Instance('collections.defaultdict', (dict,))
    metadata = Instance('collections.defaultdict', (Metadata,))
    history = List()
    debug = Bool(False)
    profile=Unicode('default')
    
    _outstanding_dict = Instance('collections.defaultdict', (set,))
    _ids = List()
    _connected=Bool(False)
    _ssh=Bool(False)
    _context = Instance('zmq.Context')
    _config = Dict()
    _engines=Instance(util.ReverseDict, (), {})
    # _hub_socket=Instance('zmq.Socket')
    _query_socket=Instance('zmq.Socket')
    _control_socket=Instance('zmq.Socket')
    _iopub_socket=Instance('zmq.Socket')
    _notification_socket=Instance('zmq.Socket')
    _mux_socket=Instance('zmq.Socket')
    _task_socket=Instance('zmq.Socket')
    _task_scheme=Unicode()
    _closed = False
    _ignored_control_replies=Int(0)
    _ignored_hub_replies=Int(0)
    
    def __init__(self, url_or_file=None, profile='default', profile_dir=None, ipython_dir=None,
            context=None, debug=False, exec_key=None,
            sshserver=None, sshkey=None, password=None, paramiko=None,
            timeout=10, **extra_args
            ):
        super(Client, self).__init__(debug=debug, profile=profile)
        if context is None:
            context = zmq.Context.instance()
        self._context = context
            
        
        self._setup_profile_dir(profile, profile_dir, ipython_dir)
        if self._cd is not None:
            if url_or_file is None:
                url_or_file = pjoin(self._cd.security_dir, 'ipcontroller-client.json')
        assert url_or_file is not None, "I can't find enough information to connect to a hub!"\
            " Please specify at least one of url_or_file or profile."
        
        try:
            util.validate_url(url_or_file)
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
        cfg['url'] = util.disambiguate_url(cfg['url'], location)
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
        
        # configure and construct the session
        if exec_key is not None:
            if os.path.isfile(exec_key):
                extra_args['keyfile'] = exec_key
            else:
                extra_args['key'] = exec_key
        self.session = Session(**extra_args)
        
        self._query_socket = self._context.socket(zmq.XREQ)
        self._query_socket.setsockopt(zmq.IDENTITY, self.session.session)
        if self._ssh:
            tunnel.tunnel_connection(self._query_socket, url, sshserver, **ssh_kwargs)
        else:
            self._query_socket.connect(url)
        
        self.session.debug = self.debug
        
        self._notification_handlers = {'registration_notification' : self._register_engine,
                                    'unregistration_notification' : self._unregister_engine,
                                    'shutdown_notification' : lambda msg: self.close(),
                                    }
        self._queue_handlers = {'execute_reply' : self._handle_execute_reply,
                                'apply_reply' : self._handle_apply_reply}
        self._connect(sshserver, ssh_kwargs, timeout)
        
    def __del__(self):
        """cleanup sockets, but _not_ context."""
        self.close()
    
    def _setup_profile_dir(self, profile, profile_dir, ipython_dir):
        if ipython_dir is None:
            ipython_dir = get_ipython_dir()
        if profile_dir is not None:
            try:
                self._cd = ProfileDir.find_profile_dir(profile_dir)
                return
            except ProfileDirError:
                pass
        elif profile is not None:
            try:
                self._cd = ProfileDir.find_profile_dir_by_name(
                    ipython_dir, profile)
                return
            except ProfileDirError:
                pass
        self._cd = None
    
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
        if not self._ids:
            # flush notification socket if no engines yet, just in case
            if not self.ids:
                raise error.NoEnginesRegistered("Can't build targets without any engines")
        
        if targets is None:
            targets = self._ids
        elif isinstance(targets, str):
            if targets.lower() == 'all':
                targets = self._ids
            else:
                raise TypeError("%r not valid str target, must be 'all'"%(targets))
        elif isinstance(targets, int):
            if targets < 0:
                targets = self.ids[targets]
            if targets not in self._ids:
                raise IndexError("No such engine: %i"%targets)
            targets = [targets]
        
        if isinstance(targets, slice):
            indices = range(len(self._ids))[targets]
            ids = self.ids
            targets = [ ids[i] for i in indices ]
        
        if not isinstance(targets, (tuple, list, xrange)):
            raise TypeError("targets by int/slice/collection of ints only, not %s"%(type(targets)))
            
        return [self._engines[t] for t in targets], list(targets)
    
    def _connect(self, sshserver, ssh_kwargs, timeout):
        """setup all our socket connections to the cluster. This is called from
        __init__."""
        
        # Maybe allow reconnecting?
        if self._connected:
            return
        self._connected=True

        def connect_socket(s, url):
            url = util.disambiguate_url(url, self._config['location'])
            if self._ssh:
                return tunnel.tunnel_connection(s, url, sshserver, **ssh_kwargs)
            else:
                return s.connect(url)
            
        self.session.send(self._query_socket, 'connection_request')
        r,w,x = zmq.select([self._query_socket],[],[], timeout)
        if not r:
            raise error.TimeoutError("Hub connection request timed out")
        idents,msg = self.session.recv(self._query_socket,mode=0)
        if self.debug:
            pprint(msg)
        msg = Message(msg)
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
        """unwrap exception, and remap engine_id to int."""
        e = error.unwrap_exception(content)
        # print e.traceback
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
            md['submitted'] = parent['date']
        if 'started' in header:
            md['started'] = header['started']
        if 'date' in header:
            md['completed'] = header['date']
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
            header['date'] = datetime.now()
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
            self.results[msg_id] = error.TaskAborted(msg_id)
        elif content['status'] == 'resubmitted':
            # TODO: handle resubmission
            pass
        else:
            self.results[msg_id] = self._unwrap_exception(content)
    
    def _flush_notifications(self):
        """Flush notifications of engine registrations waiting
        in ZMQ queue."""
        idents,msg = self.session.recv(self._notification_socket, mode=zmq.NOBLOCK)
        while msg is not None:
            if self.debug:
                pprint(msg)
            msg_type = msg['msg_type']
            handler = self._notification_handlers.get(msg_type, None)
            if handler is None:
                raise Exception("Unhandled message type: %s"%msg.msg_type)
            else:
                handler(msg)
            idents,msg = self.session.recv(self._notification_socket, mode=zmq.NOBLOCK)
    
    def _flush_results(self, sock):
        """Flush task or queue results waiting in ZMQ queue."""
        idents,msg = self.session.recv(sock, mode=zmq.NOBLOCK)
        while msg is not None:
            if self.debug:
                pprint(msg)
            msg_type = msg['msg_type']
            handler = self._queue_handlers.get(msg_type, None)
            if handler is None:
                raise Exception("Unhandled message type: %s"%msg.msg_type)
            else:
                handler(msg)
            idents,msg = self.session.recv(sock, mode=zmq.NOBLOCK)
    
    def _flush_control(self, sock):
        """Flush replies from the control channel waiting
        in the ZMQ queue.
        
        Currently: ignore them."""
        if self._ignored_control_replies <= 0:
            return
        idents,msg = self.session.recv(sock, mode=zmq.NOBLOCK)
        while msg is not None:
            self._ignored_control_replies -= 1
            if self.debug:
                pprint(msg)
            idents,msg = self.session.recv(sock, mode=zmq.NOBLOCK)
    
    def _flush_ignored_control(self):
        """flush ignored control replies"""
        while self._ignored_control_replies > 0:
            self.session.recv(self._control_socket)
            self._ignored_control_replies -= 1
    
    def _flush_ignored_hub_replies(self):
        ident,msg = self.session.recv(self._query_socket, mode=zmq.NOBLOCK)
        while msg is not None:
            ident,msg = self.session.recv(self._query_socket, mode=zmq.NOBLOCK)
    
    def _flush_iopub(self, sock):
        """Flush replies from the iopub channel waiting
        in the ZMQ queue.
        """
        idents,msg = self.session.recv(sock, mode=zmq.NOBLOCK)
        while msg is not None:
            if self.debug:
                pprint(msg)
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
            elif msg_type == 'pyin':
                md.update({'pyin' : content['code']})
            else:
                md.update({msg_type : content.get('data', '')})
            
            # reduntant?
            self.metadata[msg_id] = md
            
            idents,msg = self.session.recv(sock, mode=zmq.NOBLOCK)
    
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
            return self.direct_view(key)
    
    #--------------------------------------------------------------------------
    # Begin public methods
    #--------------------------------------------------------------------------
    
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
        if self._query_socket:
            self._flush_ignored_hub_replies()
    
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
    
    @spin_first
    def clear(self, targets=None, block=None):
        """Clear the namespace in target(s)."""
        block = self.block if block is None else block
        targets = self._build_targets(targets)[0]
        for t in targets:
            self.session.send(self._control_socket, 'clear_request', content={}, ident=t)
        error = False
        if block:
            self._flush_ignored_control()
            for i in range(len(targets)):
                idents,msg = self.session.recv(self._control_socket,0)
                if self.debug:
                    pprint(msg)
                if msg['content']['status'] != 'ok':
                    error = self._unwrap_exception(msg['content'])
        else:
            self._ignored_control_replies += len(targets)
        if error:
            raise error
        
    
    @spin_first
    def abort(self, jobs=None, targets=None, block=None):
        """Abort specific jobs from the execution queues of target(s).
        
        This is a mechanism to prevent jobs that have already been submitted
        from executing.
        
        Parameters
        ----------
        
        jobs : msg_id, list of msg_ids, or AsyncResult
            The jobs to be aborted
        
        
        """
        block = self.block if block is None else block
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
        if block:
            self._flush_ignored_control()
            for i in range(len(targets)):
                idents,msg = self.session.recv(self._control_socket,0)
                if self.debug:
                    pprint(msg)
                if msg['content']['status'] != 'ok':
                    error = self._unwrap_exception(msg['content'])
        else:
            self._ignored_control_replies += len(targets)
        if error:
            raise error
    
    @spin_first
    def shutdown(self, targets=None, restart=False, hub=False, block=None):
        """Terminates one or more engine processes, optionally including the hub."""
        block = self.block if block is None else block
        if hub:
            targets = 'all'
        targets = self._build_targets(targets)[0]
        for t in targets:
            self.session.send(self._control_socket, 'shutdown_request', 
                        content={'restart':restart},ident=t)
        error = False
        if block or hub:
            self._flush_ignored_control()
            for i in range(len(targets)):
                idents,msg = self.session.recv(self._control_socket, 0)
                if self.debug:
                    pprint(msg)
                if msg['content']['status'] != 'ok':
                    error = self._unwrap_exception(msg['content'])
        else:
            self._ignored_control_replies += len(targets)
        
        if hub:
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
    # Execution related methods
    #--------------------------------------------------------------------------
    
    def _maybe_raise(self, result):
        """wrapper for maybe raising an exception if apply failed."""
        if isinstance(result, error.RemoteError):
            raise result
        
        return result
    
    def send_apply_message(self, socket, f, args=None, kwargs=None, subheader=None, track=False,
                            ident=None):
        """construct and send an apply message via a socket.
        
        This is the principal method with which all engine execution is performed by views.
        """
                            
        assert not self._closed, "cannot use me anymore, I'm closed!"
        # defaults:
        args = args if args is not None else []
        kwargs = kwargs if kwargs is not None else {}
        subheader = subheader if subheader is not None else {}
        
        # validate arguments
        if not callable(f):
            raise TypeError("f must be callable, not %s"%type(f))
        if not isinstance(args, (tuple, list)):
            raise TypeError("args must be tuple or list, not %s"%type(args))
        if not isinstance(kwargs, dict):
            raise TypeError("kwargs must be dict, not %s"%type(kwargs))
        if not isinstance(subheader, dict):
            raise TypeError("subheader must be dict, not %s"%type(subheader))
        
        bufs = util.pack_apply_message(f,args,kwargs)
        
        msg = self.session.send(socket, "apply_request", buffers=bufs, ident=ident,
                            subheader=subheader, track=track)
        
        msg_id = msg['msg_id']
        self.outstanding.add(msg_id)
        if ident:
            # possibly routed to a specific engine
            if isinstance(ident, list):
                ident = ident[-1]
            if ident in self._engines.values():
                # save for later, in case of engine death
                self._outstanding_dict[ident].add(msg_id)
        self.history.append(msg_id)
        self.metadata[msg_id]['submitted'] = datetime.now()
        
        return msg

    #--------------------------------------------------------------------------
    # construct a View object
    #--------------------------------------------------------------------------
    
    def load_balanced_view(self, targets=None):
        """construct a DirectView object.
        
        If no arguments are specified, create a LoadBalancedView
        using all engines.
        
        Parameters
        ----------
        
        targets: list,slice,int,etc. [default: use all engines]
            The subset of engines across which to load-balance
        """
        if targets is not None:
            targets = self._build_targets(targets)[1]
        return LoadBalancedView(client=self, socket=self._task_socket, targets=targets)
    
    def direct_view(self, targets='all'):
        """construct a DirectView object.
        
        If no targets are specified, create a DirectView
        using all engines.
        
        Parameters
        ----------
        
        targets: list,slice,int,etc. [default: use all engines]
            The engines to use for the View
        """
        single = isinstance(targets, int)
        targets = self._build_targets(targets)[1]
        if single:
            targets = targets[0]
        return DirectView(client=self, socket=self._mux_socket, targets=targets)
    
    #--------------------------------------------------------------------------
    # Query methods
    #--------------------------------------------------------------------------
    
    @spin_first
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
        block = self.block if block is None else block
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

    @spin_first
    def resubmit(self, indices_or_msg_ids=None, subheader=None, block=None):
        """Resubmit one or more tasks.

        in-flight tasks may not be resubmitted.

        Parameters
        ----------

        indices_or_msg_ids : integer history index, str msg_id, or list of either
            The indices or msg_ids of indices to be retrieved

        block : bool
            Whether to wait for the result to be done

        Returns
        -------

        AsyncHubResult
            A subclass of AsyncResult that retrieves results from the Hub

        """
        block = self.block if block is None else block
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

        for msg_id in theids:
            self.outstanding.discard(msg_id)
            if msg_id in self.history:
                self.history.remove(msg_id)
            self.results.pop(msg_id, None)
            self.metadata.pop(msg_id, None)
        content = dict(msg_ids = theids)

        self.session.send(self._query_socket, 'resubmit_request', content)

        zmq.select([self._query_socket], [], [])
        idents,msg = self.session.recv(self._query_socket, zmq.NOBLOCK)
        if self.debug:
            pprint(msg)
        content = msg['content']
        if content['status'] != 'ok':
            raise self._unwrap_exception(content)

        ar = AsyncHubResult(self, msg_ids=theids)

        if block:
            ar.wait()

        return ar
    
    @spin_first
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

    @spin_first
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
        engine_ids = self._build_targets(targets)[1]
        content = dict(targets=engine_ids, verbose=verbose)
        self.session.send(self._query_socket, "queue_request", content=content)
        idents,msg = self.session.recv(self._query_socket, 0)
        if self.debug:
            pprint(msg)
        content = msg['content']
        status = content.pop('status')
        if status != 'ok':
            raise self._unwrap_exception(content)
        content = util.rekey(content)
        if isinstance(targets, int):
            return content[targets]
        else:
            return content
        
    @spin_first
    def purge_results(self, jobs=[], targets=[]):
        """Tell the Hub to forget results.
        
        Individual results can be purged by msg_id, or the entire
        history of specific targets can be purged.
        
        Parameters
        ----------
        
        jobs : str or list of str or AsyncResult objects
                the msg_ids whose results should be forgotten.
        targets : int/str/list of ints/strs
                The targets, by uuid or int_id, whose entire history is to be purged.
                Use `targets='all'` to scrub everything from the Hub's memory.
                
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

    @spin_first
    def hub_history(self):
        """Get the Hub's history
        
        Just like the Client, the Hub has a history, which is a list of msg_ids.
        This will contain the history of all clients, and, depending on configuration,
        may contain history across multiple cluster sessions.
        
        Any msg_id returned here is a valid argument to `get_result`.
        
        Returns
        -------
        
        msg_ids : list of strs
                list of all msg_ids, ordered by task submission time.
        """
        
        self.session.send(self._query_socket, "history_request", content={})
        idents, msg = self.session.recv(self._query_socket, 0)
        
        if self.debug:
            pprint(msg)
        content = msg['content']
        if content['status'] != 'ok':
            raise self._unwrap_exception(content)
        else:
            return content['history']

    @spin_first
    def db_query(self, query, keys=None):
        """Query the Hub's TaskRecord database
        
        This will return a list of task record dicts that match `query`
        
        Parameters
        ----------
        
        query : mongodb query dict
            The search dict. See mongodb query docs for details.
        keys : list of strs [optional]
            The subset of keys to be returned.  The default is to fetch everything but buffers.
            'msg_id' will *always* be included.
        """
        if isinstance(keys, basestring):
            keys = [keys]
        content = dict(query=query, keys=keys)
        self.session.send(self._query_socket, "db_request", content=content)
        idents, msg = self.session.recv(self._query_socket, 0)
        if self.debug:
            pprint(msg)
        content = msg['content']
        if content['status'] != 'ok':
            raise self._unwrap_exception(content)
        
        records = content['records']
        
        buffer_lens = content['buffer_lens']
        result_buffer_lens = content['result_buffer_lens']
        buffers = msg['buffers']
        has_bufs = buffer_lens is not None
        has_rbufs = result_buffer_lens is not None
        for i,rec in enumerate(records):
            # relink buffers
            if has_bufs:
                blen = buffer_lens[i]
                rec['buffers'], buffers = buffers[:blen],buffers[blen:]
            if has_rbufs:
                blen = result_buffer_lens[i]
                rec['result_buffers'], buffers = buffers[:blen],buffers[blen:]
            
        return records

__all__ = [ 'Client' ]
