#!/usr/bin/env python
# encoding: utf-8
"""
The IPython controller application.

Authors:

* Brian Granger
* MinRK

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import with_statement

import json
import os
import socket
import stat
import sys

from multiprocessing import Process
from signal import signal, SIGINT, SIGABRT, SIGTERM

import zmq
from zmq.devices import ProcessMonitoredQueue
from zmq.log.handlers import PUBHandler

from IPython.core.profiledir import ProfileDir

from IPython.parallel.apps.baseapp import (
    BaseParallelApplication,
    base_aliases,
    base_flags,
    catch_config_error,
)
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import Instance, Unicode, Bool, List, Dict, TraitError

from IPython.zmq.session import (
    Session, session_aliases, session_flags, default_secure
)

from IPython.parallel.controller.heartmonitor import HeartMonitor
from IPython.parallel.controller.hub import HubFactory
from IPython.parallel.controller.scheduler import TaskScheduler,launch_scheduler
from IPython.parallel.controller.sqlitedb import SQLiteDB

from IPython.parallel.util import split_url, disambiguate_url

# conditional import of MongoDB backend class

try:
    from IPython.parallel.controller.mongodb import MongoDB
except ImportError:
    maybe_mongo = []
else:
    maybe_mongo = [MongoDB]


#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------


#: The default config file name for this application
default_config_file_name = u'ipcontroller_config.py'


_description = """Start the IPython controller for parallel computing.

The IPython controller provides a gateway between the IPython engines and
clients. The controller needs to be started before the engines and can be
configured using command line options or using a cluster directory. Cluster
directories contain config, log and security files and are usually located in
your ipython directory and named as "profile_name". See the `profile`
and `profile-dir` options for details.
"""

_examples = """
ipcontroller --ip=192.168.0.1 --port=1000  # listen on ip, port for engines
ipcontroller --scheme=pure  # use the pure zeromq scheduler
"""


#-----------------------------------------------------------------------------
# The main application
#-----------------------------------------------------------------------------
flags = {}
flags.update(base_flags)
flags.update({
    'usethreads' : ( {'IPControllerApp' : {'use_threads' : True}},
                    'Use threads instead of processes for the schedulers'),
    'sqlitedb' : ({'HubFactory' : {'db_class' : 'IPython.parallel.controller.sqlitedb.SQLiteDB'}},
                    'use the SQLiteDB backend'),
    'mongodb' : ({'HubFactory' : {'db_class' : 'IPython.parallel.controller.mongodb.MongoDB'}},
                    'use the MongoDB backend'),
    'dictdb' : ({'HubFactory' : {'db_class' : 'IPython.parallel.controller.dictdb.DictDB'}},
                    'use the in-memory DictDB backend'),
    'nodb' : ({'HubFactory' : {'db_class' : 'IPython.parallel.controller.dictdb.NoDB'}},
                    """use dummy DB backend, which doesn't store any information.
                    
                    This is the default as of IPython 0.13.
                    
                    To enable delayed or repeated retrieval of results from the Hub,
                    select one of the true db backends.
                    """),
    'reuse' : ({'IPControllerApp' : {'reuse_files' : True}},
                    'reuse existing json connection files')
})

flags.update(session_flags)

aliases = dict(
    ssh = 'IPControllerApp.ssh_server',
    enginessh = 'IPControllerApp.engine_ssh_server',
    location = 'IPControllerApp.location',

    url = 'HubFactory.url',
    ip = 'HubFactory.ip',
    transport = 'HubFactory.transport',
    port = 'HubFactory.regport',

    ping = 'HeartMonitor.period',

    scheme = 'TaskScheduler.scheme_name',
    hwm = 'TaskScheduler.hwm',
)
aliases.update(base_aliases)
aliases.update(session_aliases)

class IPControllerApp(BaseParallelApplication):

    name = u'ipcontroller'
    description = _description
    examples = _examples
    config_file_name = Unicode(default_config_file_name)
    classes = [ProfileDir, Session, HubFactory, TaskScheduler, HeartMonitor, SQLiteDB] + maybe_mongo
    
    # change default to True
    auto_create = Bool(True, config=True,
        help="""Whether to create profile dir if it doesn't exist.""")
    
    reuse_files = Bool(False, config=True,
        help="""Whether to reuse existing json connection files.
        If False, connection files will be removed on a clean exit.
        """
    )
    ssh_server = Unicode(u'', config=True,
        help="""ssh url for clients to use when connecting to the Controller
        processes. It should be of the form: [user@]server[:port]. The
        Controller's listening addresses must be accessible from the ssh server""",
    )
    engine_ssh_server = Unicode(u'', config=True,
        help="""ssh url for engines to use when connecting to the Controller
        processes. It should be of the form: [user@]server[:port]. The
        Controller's listening addresses must be accessible from the ssh server""",
    )
    location = Unicode(u'', config=True,
        help="""The external IP or domain name of the Controller, used for disambiguating
        engine and client connections.""",
    )
    import_statements = List([], config=True,
        help="import statements to be run at startup.  Necessary in some environments"
    )

    use_threads = Bool(False, config=True,
        help='Use threads instead of processes for the schedulers',
    )

    engine_json_file = Unicode('ipcontroller-engine.json', config=True,
        help="JSON filename where engine connection info will be stored.")
    client_json_file = Unicode('ipcontroller-client.json', config=True,
        help="JSON filename where client connection info will be stored.")
    
    def _cluster_id_changed(self, name, old, new):
        super(IPControllerApp, self)._cluster_id_changed(name, old, new)
        self.engine_json_file = "%s-engine.json" % self.name
        self.client_json_file = "%s-client.json" % self.name


    # internal
    children = List()
    mq_class = Unicode('zmq.devices.ProcessMonitoredQueue')

    def _use_threads_changed(self, name, old, new):
        self.mq_class = 'zmq.devices.%sMonitoredQueue'%('Thread' if new else 'Process')
    
    write_connection_files = Bool(True,
        help="""Whether to write connection files to disk.
        True in all cases other than runs with `reuse_files=True` *after the first*
        """
    )

    aliases = Dict(aliases)
    flags = Dict(flags)
    

    def save_connection_dict(self, fname, cdict):
        """save a connection dict to json file."""
        c = self.config
        url = cdict['url']
        location = cdict['location']
        if not location:
            try:
                proto,ip,port = split_url(url)
            except AssertionError:
                pass
            else:
                try:
                    location = socket.gethostbyname_ex(socket.gethostname())[2][-1]
                except (socket.gaierror, IndexError):
                    self.log.warn("Could not identify this machine's IP, assuming 127.0.0.1."
                    " You may need to specify '--location=<external_ip_address>' to help"
                    " IPython decide when to connect via loopback.")
                    location = '127.0.0.1'
            cdict['location'] = location
        fname = os.path.join(self.profile_dir.security_dir, fname)
        self.log.info("writing connection info to %s", fname)
        with open(fname, 'w') as f:
            f.write(json.dumps(cdict, indent=2))
        os.chmod(fname, stat.S_IRUSR|stat.S_IWUSR)
    
    def load_config_from_json(self):
        """load config from existing json connector files."""
        c = self.config
        self.log.debug("loading config from JSON")
        # load from engine config
        fname = os.path.join(self.profile_dir.security_dir, self.engine_json_file)
        self.log.info("loading connection info from %s", fname)
        with open(fname) as f:
            cfg = json.loads(f.read())
        key = cfg['exec_key']
        # json gives unicode, Session.key wants bytes
        c.Session.key = key.encode('ascii')
        xport,addr = cfg['url'].split('://')
        c.HubFactory.engine_transport = xport
        ip,ports = addr.split(':')
        c.HubFactory.engine_ip = ip
        c.HubFactory.regport = int(ports)
        self.location = cfg['location']
        if not self.engine_ssh_server:
            self.engine_ssh_server = cfg['ssh']
        # load client config
        fname = os.path.join(self.profile_dir.security_dir, self.client_json_file)
        self.log.info("loading connection info from %s", fname)
        with open(fname) as f:
            cfg = json.loads(f.read())
        assert key == cfg['exec_key'], "exec_key mismatch between engine and client keys"
        xport,addr = cfg['url'].split('://')
        c.HubFactory.client_transport = xport
        ip,ports = addr.split(':')
        c.HubFactory.client_ip = ip
        if not self.ssh_server:
            self.ssh_server = cfg['ssh']
        assert int(ports) == c.HubFactory.regport, "regport mismatch"
    
    def cleanup_connection_files(self):
        if self.reuse_files:
            self.log.debug("leaving JSON connection files for reuse")
            return
        self.log.debug("cleaning up JSON connection files")
        for f in (self.client_json_file, self.engine_json_file):
            f = os.path.join(self.profile_dir.security_dir, f)
            try:
                os.remove(f)
            except Exception as e:
                self.log.error("Failed to cleanup connection file: %s", e)
            else:
                self.log.debug(u"removed %s", f)
    
    def load_secondary_config(self):
        """secondary config, loading from JSON and setting defaults"""
        if self.reuse_files:
            try:
                self.load_config_from_json()
            except (AssertionError,IOError) as e:
                self.log.error("Could not load config from JSON: %s" % e)
            else:
                # successfully loaded config from JSON, and reuse=True
                # no need to wite back the same file
                self.write_connection_files = False
                
        # switch Session.key default to secure
        default_secure(self.config)
        self.log.debug("Config changed")
        self.log.debug(repr(self.config))
        
    def init_hub(self):
        c = self.config
        
        self.do_import_statements()
        
        try:
            self.factory = HubFactory(config=c, log=self.log)
            # self.start_logging()
            self.factory.init_hub()
        except TraitError:
            raise
        except Exception:
            self.log.error("Couldn't construct the Controller", exc_info=True)
            self.exit(1)
        
        if self.write_connection_files:
            # save to new json config files
            f = self.factory
            cdict = {'exec_key' : f.session.key.decode('ascii'),
                    'ssh' : self.ssh_server,
                    'url' : "%s://%s:%s"%(f.client_transport, f.client_ip, f.regport),
                    'location' : self.location
                    }
            self.save_connection_dict(self.client_json_file, cdict)
            edict = cdict
            edict['url']="%s://%s:%s"%((f.client_transport, f.client_ip, f.regport))
            edict['ssh'] = self.engine_ssh_server
            self.save_connection_dict(self.engine_json_file, edict)

    def init_schedulers(self):
        children = self.children
        mq = import_item(str(self.mq_class))
        
        hub = self.factory
        # disambiguate url, in case of *
        monitor_url = disambiguate_url(hub.monitor_url)
        # maybe_inproc = 'inproc://monitor' if self.use_threads else monitor_url
        # IOPub relay (in a Process)
        q = mq(zmq.PUB, zmq.SUB, zmq.PUB, b'N/A',b'iopub')
        q.bind_in(hub.client_info['iopub'])
        q.bind_out(hub.engine_info['iopub'])
        q.setsockopt_out(zmq.SUBSCRIBE, b'')
        q.connect_mon(monitor_url)
        q.daemon=True
        children.append(q)

        # Multiplexer Queue (in a Process)
        q = mq(zmq.ROUTER, zmq.ROUTER, zmq.PUB, b'in', b'out')
        q.bind_in(hub.client_info['mux'])
        q.setsockopt_in(zmq.IDENTITY, b'mux')
        q.bind_out(hub.engine_info['mux'])
        q.connect_mon(monitor_url)
        q.daemon=True
        children.append(q)

        # Control Queue (in a Process)
        q = mq(zmq.ROUTER, zmq.ROUTER, zmq.PUB, b'incontrol', b'outcontrol')
        q.bind_in(hub.client_info['control'])
        q.setsockopt_in(zmq.IDENTITY, b'control')
        q.bind_out(hub.engine_info['control'])
        q.connect_mon(monitor_url)
        q.daemon=True
        children.append(q)
        try:
            scheme = self.config.TaskScheduler.scheme_name
        except AttributeError:
            scheme = TaskScheduler.scheme_name.get_default_value()
        # Task Queue (in a Process)
        if scheme == 'pure':
            self.log.warn("task::using pure DEALER Task scheduler")
            q = mq(zmq.ROUTER, zmq.DEALER, zmq.PUB, b'intask', b'outtask')
            # q.setsockopt_out(zmq.HWM, hub.hwm)
            q.bind_in(hub.client_info['task'][1])
            q.setsockopt_in(zmq.IDENTITY, b'task')
            q.bind_out(hub.engine_info['task'])
            q.connect_mon(monitor_url)
            q.daemon=True
            children.append(q)
        elif scheme == 'none':
            self.log.warn("task::using no Task scheduler")

        else:
            self.log.info("task::using Python %s Task scheduler"%scheme)
            sargs = (hub.client_info['task'][1], hub.engine_info['task'],
                                monitor_url, disambiguate_url(hub.client_info['notification']))
            kwargs = dict(logname='scheduler', loglevel=self.log_level,
                            log_url = self.log_url, config=dict(self.config))
            if 'Process' in self.mq_class:
                # run the Python scheduler in a Process
                q = Process(target=launch_scheduler, args=sargs, kwargs=kwargs)
                q.daemon=True
                children.append(q)
            else:
                # single-threaded Controller
                kwargs['in_thread'] = True
                launch_scheduler(*sargs, **kwargs)

    def terminate_children(self):
        child_procs = []
        for child in self.children:
            if isinstance(child, ProcessMonitoredQueue):
                child_procs.append(child.launcher)
            elif isinstance(child, Process):
                child_procs.append(child)
        if child_procs:
            self.log.critical("terminating children...")
            for child in child_procs:
                try:
                    child.terminate()
                except OSError:
                    # already dead
                    pass
    
    def handle_signal(self, sig, frame):
        self.log.critical("Received signal %i, shutting down", sig)
        self.terminate_children()
        self.loop.stop()
    
    def init_signal(self):
        for sig in (SIGINT, SIGABRT, SIGTERM):
            signal(sig, self.handle_signal)

    def do_import_statements(self):
        statements = self.import_statements
        for s in statements:
            try:
                self.log.msg("Executing statement: '%s'" % s)
                exec s in globals(), locals()
            except:
                self.log.msg("Error running statement: %s" % s)

    def forward_logging(self):
        if self.log_url:
            self.log.info("Forwarding logging to %s"%self.log_url)
            context = zmq.Context.instance()
            lsock = context.socket(zmq.PUB)
            lsock.connect(self.log_url)
            handler = PUBHandler(lsock)
            handler.root_topic = 'controller'
            handler.setLevel(self.log_level)
            self.log.addHandler(handler)
    
    @catch_config_error
    def initialize(self, argv=None):
        super(IPControllerApp, self).initialize(argv)
        self.forward_logging()
        self.load_secondary_config()
        self.init_hub()
        self.init_schedulers()
    
    def start(self):
        # Start the subprocesses:
        self.factory.start()
        # children must be started before signals are setup,
        # otherwise signal-handling will fire multiple times
        for child in self.children:
            child.start()
        self.init_signal()

        self.write_pid_file(overwrite=True)

        try:
            self.factory.loop.start()
        except KeyboardInterrupt:
            self.log.critical("Interrupted, Exiting...\n")
        finally:
            self.cleanup_connection_files()
            


def launch_new_instance():
    """Create and run the IPython controller"""
    if sys.platform == 'win32':
        # make sure we don't get called from a multiprocessing subprocess
        # this can result in infinite Controllers being started on Windows
        # which doesn't have a proper fork, so multiprocessing is wonky
        
        # this only comes up when IPython has been installed using vanilla
        # setuptools, and *not* distribute.
        import multiprocessing
        p = multiprocessing.current_process()
        # the main process has name 'MainProcess'
        # subprocesses will have names like 'Process-1'
        if p.name != 'MainProcess':
            # we are a subprocess, don't start another Controller!
            return
    app = IPControllerApp.instance()
    app.initialize()
    app.start()


if __name__ == '__main__':
    launch_new_instance()
