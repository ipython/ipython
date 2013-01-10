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
import sys
from threading import Thread, Event
import time
import warnings
from datetime import datetime
from getpass import getpass
from pprint import pprint

pjoin = os.path.join

import zmq
# from zmq.eventloop import ioloop, zmqstream

from IPython.config.configurable import MultipleInstanceError
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir, ProfileDirError

from IPython.utils.coloransi import TermColors
from IPython.utils.jsonutil import rekey
from IPython.utils.localinterfaces import LOCAL_IPS
from IPython.utils.path import get_ipython_dir
from IPython.utils.py3compat import cast_bytes
from IPython.utils.traitlets import (HasTraits, Integer, Instance, Unicode,
                                    Dict, List, Bool, Set, Any)
from IPython.external.decorator import decorator
from IPython.external.ssh import tunnel

from IPython.parallel import Reference
from IPython.parallel import error
from IPython.parallel import util

from IPython.zmq.session import Session, Message
from IPython.zmq import serialize

from .asyncresult import AsyncResult, AsyncHubResult
from .view import DirectView, LoadBalancedView

if sys.version_info[0] >= 3:
    # xrange is used in a couple 'isinstance' tests in py2
    # should be just 'range' in 3k
    xrange = range

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


class ExecuteReply(object):
    """wrapper for finished Execute results"""
    def __init__(self, msg_id, content, metadata):
        self.msg_id = msg_id
        self._content = content
        self.execution_count = content['execution_count']
        self.metadata = metadata
    
    def __getitem__(self, key):
        return self.metadata[key]
    
    def __getattr__(self, key):
        if key not in self.metadata:
            raise AttributeError(key)
        return self.metadata[key]
    
    def __repr__(self):
        pyout = self.metadata['pyout'] or {'data':{}}
        text_out = pyout['data'].get('text/plain', '')
        if len(text_out) > 32:
            text_out = text_out[:29] + '...'
        
        return "<ExecuteReply[%i]: %s>" % (self.execution_count, text_out)
    
    def _repr_pretty_(self, p, cycle):
        pyout = self.metadata['pyout'] or {'data':{}}
        text_out = pyout['data'].get('text/plain', '')
        
        if not text_out:
            return
        
        try:
            ip = get_ipython()
        except NameError:
            colors = "NoColor"
        else:
            colors = ip.colors
        
        if colors == "NoColor":
            out = normal = ""
        else:
            out = TermColors.Red
            normal = TermColors.Normal
        
        if '\n' in text_out and not text_out.startswith('\n'):
            # add newline for multiline reprs
            text_out = '\n' + text_out
        
        p.text(
            out + u'Out[%i:%i]: ' % (
                self.metadata['engine_id'], self.execution_count
            ) + normal + text_out
        )
    
    def _repr_html_(self):
        pyout = self.metadata['pyout'] or {'data':{}}
        return pyout['data'].get("text/html")
    
    def _repr_latex_(self):
        pyout = self.metadata['pyout'] or {'data':{}}
        return pyout['data'].get("text/latex")
    
    def _repr_json_(self):
        pyout = self.metadata['pyout'] or {'data':{}}
        return pyout['data'].get("application/json")
    
    def _repr_javascript_(self):
        pyout = self.metadata['pyout'] or {'data':{}}
        return pyout['data'].get("application/javascript")
    
    def _repr_png_(self):
        pyout = self.metadata['pyout'] or {'data':{}}
        return pyout['data'].get("image/png")
    
    def _repr_jpeg_(self):
        pyout = self.metadata['pyout'] or {'data':{}}
        return pyout['data'].get("image/jpeg")
    
    def _repr_svg_(self):
        pyout = self.metadata['pyout'] or {'data':{}}
        return pyout['data'].get("image/svg+xml")


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
              'outputs' : [],
              'data': {},
              'outputs_ready' : False,
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

    url_file : str/unicode; path to ipcontroller-client.json
        This JSON file should contain all the information needed to connect to a cluster,
        and is likely the only argument needed.
        Connection information for the Hub's registration.  If a json connector
        file is given, then likely no further configuration is necessary.
        [Default: use profile]
    profile : bytes
        The name of the Cluster profile to be used to find connector information.
        If run from an IPython application, the default profile will be the same
        as the running application, otherwise it will be 'default'.
    cluster_id : str
        String id to added to runtime files, to prevent name collisions when using
        multiple clusters with a single profile simultaneously.
        When set, will look for files named like: 'ipcontroller-<cluster_id>-client.json'
        Since this is text inserted into filenames, typical recommendations apply:
        Simple character strings are ideal, and spaces are not recommended (but
        should generally work)
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
    sshkey : str; path to ssh private key file
        This specifies a key to be used in ssh login, default None.
        Regular default ssh keys will be used without specifying this argument.
    password : str
        Your ssh password to sshserver. Note that if this is left None,
        you will be prompted for it if passwordless key based login is unavailable.
    paramiko : bool
        flag for whether to use paramiko instead of shell ssh for tunneling.
        [default: True on win32, False else]


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
    _spin_thread = Any()
    _stop_spinning = Any()

    profile=Unicode()
    def _profile_default(self):
        if BaseIPythonApplication.initialized():
            # an IPython app *might* be running, try to get its profile
            try:
                return BaseIPythonApplication.instance().profile
            except (AttributeError, MultipleInstanceError):
                # could be a *different* subclass of config.Application,
                # which would raise one of these two errors.
                return u'default'
        else:
            return u'default'


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
    _ignored_control_replies=Integer(0)
    _ignored_hub_replies=Integer(0)

    def __new__(self, *args, **kw):
        # don't raise on positional args
        return HasTraits.__new__(self, **kw)

    def __init__(self, url_file=None, profile=None, profile_dir=None, ipython_dir=None,
            context=None, debug=False,
            sshserver=None, sshkey=None, password=None, paramiko=None,
            timeout=10, cluster_id=None, **extra_args
            ):
        if profile:
            super(Client, self).__init__(debug=debug, profile=profile)
        else:
            super(Client, self).__init__(debug=debug)
        if context is None:
            context = zmq.Context.instance()
        self._context = context
        self._stop_spinning = Event()
        
        if 'url_or_file' in extra_args:
            url_file = extra_args['url_or_file']
            warnings.warn("url_or_file arg no longer supported, use url_file", DeprecationWarning)
        
        if url_file and util.is_url(url_file):
            raise ValueError("single urls cannot be specified, url-files must be used.")

        self._setup_profile_dir(self.profile, profile_dir, ipython_dir)
        
        if self._cd is not None:
            if url_file is None:
                if not cluster_id:
                    client_json = 'ipcontroller-client.json'
                else:
                    client_json = 'ipcontroller-%s-client.json' % cluster_id
                url_file = pjoin(self._cd.security_dir, client_json)
        if url_file is None:
            raise ValueError(
                "I can't find enough information to connect to a hub!"
                " Please specify at least one of url_file or profile."
            )
        
        with open(url_file) as f:
            cfg = json.load(f)
        
        self._task_scheme = cfg['task_scheme']

        # sync defaults from args, json:
        if sshserver:
            cfg['ssh'] = sshserver

        location = cfg.setdefault('location', None)
        
        proto,addr = cfg['interface'].split('://')
        addr = util.disambiguate_ip_address(addr, location)
        cfg['interface'] = "%s://%s" % (proto, addr)
        
        # turn interface,port into full urls:
        for key in ('control', 'task', 'mux', 'iopub', 'notification', 'registration'):
            cfg[key] = cfg['interface'] + ':%i' % cfg[key]
        
        url = cfg['registration']
        
        if location is not None and addr == '127.0.0.1':
            # location specified, and connection is expected to be local
            if location not in LOCAL_IPS and not sshserver:
                # load ssh from JSON *only* if the controller is not on
                # this machine
                sshserver=cfg['ssh']
            if location not in LOCAL_IPS and not sshserver:
                # warn if no ssh specified, but SSH is probably needed
                # This is only a warning, because the most likely cause
                # is a local Controller on a laptop whose IP is dynamic
                warnings.warn("""
            Controller appears to be listening on localhost, but not on this machine.
            If this is true, you should specify Client(...,sshserver='you@%s')
            or instruct your controller to listen on an external IP."""%location,
                RuntimeWarning)
        elif not sshserver:
            # otherwise sync with cfg
            sshserver = cfg['ssh']

        self._config = cfg

        self._ssh = bool(sshserver or sshkey or password)
        if self._ssh and sshserver is None:
            # default to ssh via localhost
            sshserver = addr
        if self._ssh and password is None:
            if tunnel.try_passwordless_ssh(sshserver, sshkey, paramiko):
                password=False
            else:
                password = getpass("SSH Password for %s: "%sshserver)
        ssh_kwargs = dict(keyfile=sshkey, password=password, paramiko=paramiko)

        # configure and construct the session
        extra_args['packer'] = cfg['pack']
        extra_args['unpacker'] = cfg['unpack']
        extra_args['key'] = cast_bytes(cfg['exec_key'])
        
        self.session = Session(**extra_args)

        self._query_socket = self._context.socket(zmq.DEALER)

        if self._ssh:
            tunnel.tunnel_connection(self._query_socket, cfg['registration'], sshserver, **ssh_kwargs)
        else:
            self._query_socket.connect(cfg['registration'])

        self.session.debug = self.debug

        self._notification_handlers = {'registration_notification' : self._register_engine,
                                    'unregistration_notification' : self._unregister_engine,
                                    'shutdown_notification' : lambda msg: self.close(),
                                    }
        self._queue_handlers = {'execute_reply' : self._handle_execute_reply,
                                'apply_reply' : self._handle_apply_reply}
        self._connect(sshserver, ssh_kwargs, timeout)
        
        # last step: setup magics, if we are in IPython:
        
        try:
            ip = get_ipython()
        except NameError:
            return
        else:
            if 'px' not in ip.magics_manager.magics:
                # in IPython but we are the first Client.
                # activate a default view for parallel magics.
                self.activate()

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
            if eid not in self._engines:
                self._ids.append(eid)
            self._engines[eid] = v
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
        elif isinstance(targets, basestring):
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

        return [cast_bytes(self._engines[t]) for t in targets], list(targets)

    def _connect(self, sshserver, ssh_kwargs, timeout):
        """setup all our socket connections to the cluster. This is called from
        __init__."""

        # Maybe allow reconnecting?
        if self._connected:
            return
        self._connected=True

        def connect_socket(s, url):
            # url = util.disambiguate_url(url, self._config['location'])
            if self._ssh:
                return tunnel.tunnel_connection(s, url, sshserver, **ssh_kwargs)
            else:
                return s.connect(url)

        self.session.send(self._query_socket, 'connection_request')
        # use Poller because zmq.select has wrong units in pyzmq 2.1.7
        poller = zmq.Poller()
        poller.register(self._query_socket, zmq.POLLIN)
        # poll expects milliseconds, timeout is seconds
        evts = poller.poll(timeout*1000)
        if not evts:
            raise error.TimeoutError("Hub connection request timed out")
        idents,msg = self.session.recv(self._query_socket,mode=0)
        if self.debug:
            pprint(msg)
        content = msg['content']
        # self._config['registration'] = dict(content)
        cfg = self._config
        if content['status'] == 'ok':
            self._mux_socket = self._context.socket(zmq.DEALER)
            connect_socket(self._mux_socket, cfg['mux'])

            self._task_socket = self._context.socket(zmq.DEALER)
            connect_socket(self._task_socket, cfg['task'])

            self._notification_socket = self._context.socket(zmq.SUB)
            self._notification_socket.setsockopt(zmq.SUBSCRIBE, b'')
            connect_socket(self._notification_socket, cfg['notification'])

            self._control_socket = self._context.socket(zmq.DEALER)
            connect_socket(self._control_socket, cfg['control'])

            self._iopub_socket = self._context.socket(zmq.SUB)
            self._iopub_socket.setsockopt(zmq.SUBSCRIBE, b'')
            connect_socket(self._iopub_socket, cfg['iopub'])

            self._update_engines(dict(content['engines']))
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

    def _extract_metadata(self, msg):
        header = msg['header']
        parent = msg['parent_header']
        msg_meta = msg['metadata']
        content = msg['content']
        md = {'msg_id' : parent['msg_id'],
              'received' : datetime.now(),
              'engine_uuid' : msg_meta.get('engine', None),
              'follow' : msg_meta.get('follow', []),
              'after' : msg_meta.get('after', []),
              'status' : content['status'],
            }

        if md['engine_uuid'] is not None:
            md['engine_id'] = self._engines.get(md['engine_uuid'], None)

        if 'date' in parent:
            md['submitted'] = parent['date']
        if 'started' in msg_meta:
            md['started'] = msg_meta['started']
        if 'date' in header:
            md['completed'] = header['date']
        return md

    def _register_engine(self, msg):
        """Register a new engine, and update our connection info."""
        content = msg['content']
        eid = content['id']
        d = {eid : content['uuid']}
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
            msg = self.session.msg('apply_reply', content=content)
            msg['parent_header']['msg_id'] = msg_id
            msg['metadata']['engine'] = uuid
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

        content = msg['content']
        header = msg['header']

        # construct metadata:
        md = self.metadata[msg_id]
        md.update(self._extract_metadata(msg))
        # is this redundant?
        self.metadata[msg_id] = md
        
        e_outstanding = self._outstanding_dict[md['engine_uuid']]
        if msg_id in e_outstanding:
            e_outstanding.remove(msg_id)

        # construct result:
        if content['status'] == 'ok':
            self.results[msg_id] = ExecuteReply(msg_id, content, md)
        elif content['status'] == 'aborted':
            self.results[msg_id] = error.TaskAborted(msg_id)
        elif content['status'] == 'resubmitted':
            # TODO: handle resubmission
            pass
        else:
            self.results[msg_id] = self._unwrap_exception(content)

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
        md.update(self._extract_metadata(msg))
        # is this redundant?
        self.metadata[msg_id] = md

        e_outstanding = self._outstanding_dict[md['engine_uuid']]
        if msg_id in e_outstanding:
            e_outstanding.remove(msg_id)

        # construct result:
        if content['status'] == 'ok':
            self.results[msg_id] = serialize.unserialize_object(msg['buffers'])[0]
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
            msg_type = msg['header']['msg_type']
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
            msg_type = msg['header']['msg_type']
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
            # ignore IOPub messages with no parent.
            # Caused by print statements or warnings from before the first execution.
            if not parent:
                continue
            msg_id = parent['msg_id']
            content = msg['content']
            header = msg['header']
            msg_type = msg['header']['msg_type']

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
            elif msg_type == 'display_data':
                md['outputs'].append(content)
            elif msg_type == 'pyout':
                md['pyout'] = content
            elif msg_type == 'data_message':
                data, remainder = serialize.unserialize_object(msg['buffers'])
                md['data'].update(data)
            elif msg_type == 'status':
                # idle message comes after all outputs
                if content['execution_state'] == 'idle':
                    md['outputs_ready'] = True
            else:
                # unhandled msg_type (status, etc.)
                pass

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

    def activate(self, targets='all', suffix=''):
        """Create a DirectView and register it with IPython magics
        
        Defines the magics `%px, %autopx, %pxresult, %%px`
        
        Parameters
        ----------
        
        targets: int, list of ints, or 'all'
            The engines on which the view's magics will run
        suffix: str [default: '']
            The suffix, if any, for the magics.  This allows you to have
            multiple views associated with parallel magics at the same time.
            
            e.g. ``rc.activate(targets=0, suffix='0')`` will give you
            the magics ``%px0``, ``%pxresult0``, etc. for running magics just
            on engine 0.
        """
        view = self.direct_view(targets)
        view.block = True
        view.activate(suffix)
        return view

    def close(self):
        if self._closed:
            return
        self.stop_spin_thread()
        snames = filter(lambda n: n.endswith('socket'), dir(self))
        for socket in map(lambda name: getattr(self, name), snames):
            if isinstance(socket, zmq.Socket) and not socket.closed:
                socket.close()
        self._closed = True

    def _spin_every(self, interval=1):
        """target func for use in spin_thread"""
        while True:
            if self._stop_spinning.is_set():
                return
            time.sleep(interval)
            self.spin()

    def spin_thread(self, interval=1):
        """call Client.spin() in a background thread on some regular interval
        
        This helps ensure that messages don't pile up too much in the zmq queue
        while you are working on other things, or just leaving an idle terminal.
        
        It also helps limit potential padding of the `received` timestamp
        on AsyncResult objects, used for timings.
        
        Parameters
        ----------
        
        interval : float, optional
            The interval on which to spin the client in the background thread
            (simply passed to time.sleep).
        
        Notes
        -----
        
        For precision timing, you may want to use this method to put a bound
        on the jitter (in seconds) in `received` timestamps used
        in AsyncResult.wall_time.
        
        """
        if self._spin_thread is not None:
            self.stop_spin_thread()
        self._stop_spinning.clear()
        self._spin_thread = Thread(target=self._spin_every, args=(interval,))
        self._spin_thread.daemon = True
        self._spin_thread.start()
    
    def stop_spin_thread(self):
        """stop background spin_thread, if any"""
        if self._spin_thread is not None:
            self._stop_spinning.set()
            self._spin_thread.join()
            self._spin_thread = None

    def spin(self):
        """Flush any registration notifications and execution results
        waiting in the ZMQ queue.
        """
        if self._notification_socket:
            self._flush_notifications()
        if self._iopub_socket:
            self._flush_iopub(self._iopub_socket)
        if self._mux_socket:
            self._flush_results(self._mux_socket)
        if self._task_socket:
            self._flush_results(self._task_socket)
        if self._control_socket:
            self._flush_control(self._control_socket)
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
            if isinstance(jobs, (int, basestring, AsyncResult)):
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
            
            If unspecified/None: abort all outstanding jobs.

        """
        block = self.block if block is None else block
        jobs = jobs if jobs is not None else list(self.outstanding)
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
    def shutdown(self, targets='all', restart=False, hub=False, block=None):
        """Terminates one or more engine processes, optionally including the hub.
        
        Parameters
        ----------
        
        targets: list of ints or 'all' [default: all]
            Which engines to shutdown.
        hub: bool [default: False]
            Whether to include the Hub.  hub=True implies targets='all'.
        block: bool [default: self.block]
            Whether to wait for clean shutdown replies or not.
        restart: bool [default: False]
            NOT IMPLEMENTED
            whether to restart engines after shutting them down.
        """
        from IPython.parallel.error import NoEnginesRegistered
        if restart:
            raise NotImplementedError("Engine restart is not yet implemented")
        
        block = self.block if block is None else block
        if hub:
            targets = 'all'
        try:
            targets = self._build_targets(targets)[0]
        except NoEnginesRegistered:
            targets = []
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

    def send_apply_request(self, socket, f, args=None, kwargs=None, metadata=None, track=False,
                            ident=None):
        """construct and send an apply message via a socket.

        This is the principal method with which all engine execution is performed by views.
        """

        if self._closed:
            raise RuntimeError("Client cannot be used after its sockets have been closed")
        
        # defaults:
        args = args if args is not None else []
        kwargs = kwargs if kwargs is not None else {}
        metadata = metadata if metadata is not None else {}

        # validate arguments
        if not callable(f) and not isinstance(f, Reference):
            raise TypeError("f must be callable, not %s"%type(f))
        if not isinstance(args, (tuple, list)):
            raise TypeError("args must be tuple or list, not %s"%type(args))
        if not isinstance(kwargs, dict):
            raise TypeError("kwargs must be dict, not %s"%type(kwargs))
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be dict, not %s"%type(metadata))

        bufs = serialize.pack_apply_message(f, args, kwargs,
            buffer_threshold=self.session.buffer_threshold,
            item_threshold=self.session.item_threshold,
        )

        msg = self.session.send(socket, "apply_request", buffers=bufs, ident=ident,
                            metadata=metadata, track=track)

        msg_id = msg['header']['msg_id']
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

    def send_execute_request(self, socket, code, silent=True, metadata=None, ident=None):
        """construct and send an execute request via a socket.

        """

        if self._closed:
            raise RuntimeError("Client cannot be used after its sockets have been closed")
        
        # defaults:
        metadata = metadata if metadata is not None else {}

        # validate arguments
        if not isinstance(code, basestring):
            raise TypeError("code must be text, not %s" % type(code))
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be dict, not %s" % type(metadata))
        
        content = dict(code=code, silent=bool(silent), user_variables=[], user_expressions={})


        msg = self.session.send(socket, "execute_request", content=content, ident=ident,
                            metadata=metadata)

        msg_id = msg['header']['msg_id']
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
        if targets == 'all':
            targets = None
        if targets is not None:
            targets = self._build_targets(targets)[1]
        return LoadBalancedView(client=self, socket=self._task_socket, targets=targets)

    def direct_view(self, targets='all'):
        """construct a DirectView object.

        If no targets are specified, create a DirectView using all engines.
        
        rc.direct_view('all') is distinguished from rc[:] in that 'all' will
        evaluate the target engines at each execution, whereas rc[:] will connect to
        all *current* engines, and that list will not change.
        
        That is, 'all' will always use all engines, whereas rc[:] will not use
        engines added after the DirectView is constructed.

        Parameters
        ----------

        targets: list,slice,int,etc. [default: use all engines]
            The engines to use for the View
        """
        single = isinstance(targets, int)
        # allow 'all' to be lazily evaluated at each execution
        if targets != 'all':
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
            if not isinstance(id, basestring):
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
    def resubmit(self, indices_or_msg_ids=None, metadata=None, block=None):
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
            if not isinstance(id, basestring):
                raise TypeError("indices must be str or int, not %r"%id)
            theids.append(id)

        content = dict(msg_ids = theids)

        self.session.send(self._query_socket, 'resubmit_request', content)

        zmq.select([self._query_socket], [], [])
        idents,msg = self.session.recv(self._query_socket, zmq.NOBLOCK)
        if self.debug:
            pprint(msg)
        content = msg['content']
        if content['status'] != 'ok':
            raise self._unwrap_exception(content)
        mapping = content['resubmitted']
        new_ids = [ mapping[msg_id] for msg_id in theids ]

        ar = AsyncHubResult(self, msg_ids=new_ids)

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
                md_msg = dict(
                    content=rcontent,
                    parent_header=parent,
                    header=header,
                    metadata=rec['result_metadata'],
                )
                md.update(self._extract_metadata(md_msg))
                if rec.get('received'):
                    md['received'] = rec['received']
                md.update(iodict)
                
                if rcontent['status'] == 'ok':
                    if header['msg_type'] == 'apply_reply':
                        res,buffers = serialize.unserialize_object(buffers)
                    elif header['msg_type'] == 'execute_reply':
                        res = ExecuteReply(msg_id, rcontent, md)
                    else:
                        raise KeyError("unhandled msg type: %r" % header[msg_type])
                else:
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
        if targets == 'all':
            # allow 'all' to be evaluated on the engine
            engine_ids = None
        else:
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
        content = rekey(content)
        if isinstance(targets, int):
            return content[targets]
        else:
            return content

    @spin_first
    def purge_results(self, jobs=[], targets=[]):
        """Tell the Hub to forget results.

        Individual results can be purged by msg_id, or the entire
        history of specific targets can be purged.

        Use `purge_results('all')` to scrub everything from the Hub's db.

        Parameters
        ----------

        jobs : str or list of str or AsyncResult objects
                the msg_ids whose results should be forgotten.
        targets : int/str/list of ints/strs
                The targets, by int_id, whose entire history is to be purged.

                default : None
        """
        if not targets and not jobs:
            raise ValueError("Must specify at least one of `targets` and `jobs`")
        if targets:
            targets = self._build_targets(targets)[1]

        # construct msg_ids from jobs
        if jobs == 'all':
            msg_ids = jobs
        else:
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

        content = dict(engine_ids=targets, msg_ids=msg_ids)
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
