#!/usr/bin/env python
# encoding: utf-8
"""
The IPython controller application.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import with_statement

import os
import socket
import stat
import sys
import uuid

from multiprocessing import Process

import zmq
from zmq.devices import ProcessMonitoredQueue
from zmq.log.handlers import PUBHandler
from zmq.utils import jsonapi as json

from IPython.core.newapplication import ProfileDir

from IPython.parallel.apps.baseapp import (
    BaseParallelApplication,
    base_flags
)
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import Instance, Unicode, Bool, List, Dict

# from IPython.parallel.controller.controller import ControllerFactory
from IPython.parallel.streamsession import StreamSession
from IPython.parallel.controller.heartmonitor import HeartMonitor
from IPython.parallel.controller.hub import HubFactory
from IPython.parallel.controller.scheduler import TaskScheduler,launch_scheduler
from IPython.parallel.controller.sqlitedb import SQLiteDB

from IPython.parallel.util import signal_children, split_url

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
your ipython directory and named as "cluster_<profile>". See the `profile`
and `profile_dir` options for details.
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
    'reuse' : ({'IPControllerApp' : {'reuse_files' : True}},
                    'reuse existing json connection files')
})

flags.update()

class IPControllerApp(BaseParallelApplication):

    name = u'ipcontroller'
    description = _description
    config_file_name = Unicode(default_config_file_name)
    classes = [ProfileDir, StreamSession, HubFactory, TaskScheduler, HeartMonitor, SQLiteDB] + maybe_mongo
    
    # change default to True
    auto_create = Bool(True, config=True,
        help="""Whether to create profile dir if it doesn't exist""")
    
    reuse_files = Bool(False, config=True,
        help='Whether to reuse existing json connection files [default: False]'
    )
    secure = Bool(True, config=True,
        help='Whether to use exec_keys for extra authentication [default: True]'
    )
    ssh_server = Unicode(u'', config=True,
        help="""ssh url for clients to use when connecting to the Controller
        processes. It should be of the form: [user@]server[:port]. The
        Controller\'s listening addresses must be accessible from the ssh server""",
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

    # internal
    children = List()
    mq_class = Unicode('zmq.devices.ProcessMonitoredQueue')

    def _use_threads_changed(self, name, old, new):
        self.mq_class = 'zmq.devices.%sMonitoredQueue'%('Thread' if new else 'Process')

    aliases = Dict(dict(
        log_level = 'IPControllerApp.log_level',
        log_url = 'IPControllerApp.log_url',
        reuse_files = 'IPControllerApp.reuse_files',
        secure = 'IPControllerApp.secure',
        ssh = 'IPControllerApp.ssh_server',
        use_threads = 'IPControllerApp.use_threads',
        import_statements = 'IPControllerApp.import_statements',
        location = 'IPControllerApp.location',

        ident = 'StreamSession.session',
        user = 'StreamSession.username',
        exec_key = 'StreamSession.keyfile',

        url = 'HubFactory.url',
        ip = 'HubFactory.ip',
        transport = 'HubFactory.transport',
        port = 'HubFactory.regport',

        ping = 'HeartMonitor.period',

        scheme = 'TaskScheduler.scheme_name',
        hwm = 'TaskScheduler.hwm',


        profile = "BaseIPythonApplication.profile",
        profile_dir = 'ProfileDir.location',
        
    ))
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
                location = socket.gethostbyname_ex(socket.gethostname())[2][-1]
            cdict['location'] = location
        fname = os.path.join(self.profile_dir.security_dir, fname)
        with open(fname, 'w') as f:
            f.write(json.dumps(cdict, indent=2))
        os.chmod(fname, stat.S_IRUSR|stat.S_IWUSR)
    
    def load_config_from_json(self):
        """load config from existing json connector files."""
        c = self.config
        # load from engine config
        with open(os.path.join(self.profile_dir.security_dir, 'ipcontroller-engine.json')) as f:
            cfg = json.loads(f.read())
        key = c.StreamSession.key = cfg['exec_key']
        xport,addr = cfg['url'].split('://')
        c.HubFactory.engine_transport = xport
        ip,ports = addr.split(':')
        c.HubFactory.engine_ip = ip
        c.HubFactory.regport = int(ports)
        self.location = cfg['location']
        
        # load client config
        with open(os.path.join(self.profile_dir.security_dir, 'ipcontroller-client.json')) as f:
            cfg = json.loads(f.read())
        assert key == cfg['exec_key'], "exec_key mismatch between engine and client keys"
        xport,addr = cfg['url'].split('://')
        c.HubFactory.client_transport = xport
        ip,ports = addr.split(':')
        c.HubFactory.client_ip = ip
        self.ssh_server = cfg['ssh']
        assert int(ports) == c.HubFactory.regport, "regport mismatch"
    
    def init_hub(self):
        c = self.config
        
        self.do_import_statements()
        reusing = self.reuse_files
        if reusing:
            try:
                self.load_config_from_json()
            except (AssertionError,IOError):
                reusing=False
        # check again, because reusing may have failed:
        if reusing:
            pass
        elif self.secure:
            key = str(uuid.uuid4())
            # keyfile = os.path.join(self.profile_dir.security_dir, self.exec_key)
            # with open(keyfile, 'w') as f:
            #     f.write(key)
            # os.chmod(keyfile, stat.S_IRUSR|stat.S_IWUSR)
            c.StreamSession.key = key
        else:
            key = c.StreamSession.key = ''
        
        try:
            self.factory = HubFactory(config=c, log=self.log)
            # self.start_logging()
            self.factory.init_hub()
        except:
            self.log.error("Couldn't construct the Controller", exc_info=True)
            self.exit(1)
        
        if not reusing:
            # save to new json config files
            f = self.factory
            cdict = {'exec_key' : key,
                    'ssh' : self.ssh_server,
                    'url' : "%s://%s:%s"%(f.client_transport, f.client_ip, f.regport),
                    'location' : self.location
                    }
            self.save_connection_dict('ipcontroller-client.json', cdict)
            edict = cdict
            edict['url']="%s://%s:%s"%((f.client_transport, f.client_ip, f.regport))
            self.save_connection_dict('ipcontroller-engine.json', edict)

    #
    def init_schedulers(self):
        children = self.children
        mq = import_item(str(self.mq_class))
        
        hub = self.factory
        # maybe_inproc = 'inproc://monitor' if self.use_threads else self.monitor_url
        # IOPub relay (in a Process)
        q = mq(zmq.PUB, zmq.SUB, zmq.PUB, 'N/A','iopub')
        q.bind_in(hub.client_info['iopub'])
        q.bind_out(hub.engine_info['iopub'])
        q.setsockopt_out(zmq.SUBSCRIBE, '')
        q.connect_mon(hub.monitor_url)
        q.daemon=True
        children.append(q)

        # Multiplexer Queue (in a Process)
        q = mq(zmq.XREP, zmq.XREP, zmq.PUB, 'in', 'out')
        q.bind_in(hub.client_info['mux'])
        q.setsockopt_in(zmq.IDENTITY, 'mux')
        q.bind_out(hub.engine_info['mux'])
        q.connect_mon(hub.monitor_url)
        q.daemon=True
        children.append(q)

        # Control Queue (in a Process)
        q = mq(zmq.XREP, zmq.XREP, zmq.PUB, 'incontrol', 'outcontrol')
        q.bind_in(hub.client_info['control'])
        q.setsockopt_in(zmq.IDENTITY, 'control')
        q.bind_out(hub.engine_info['control'])
        q.connect_mon(hub.monitor_url)
        q.daemon=True
        children.append(q)
        try:
            scheme = self.config.TaskScheduler.scheme_name
        except AttributeError:
            scheme = TaskScheduler.scheme_name.get_default_value()
        # Task Queue (in a Process)
        if scheme == 'pure':
            self.log.warn("task::using pure XREQ Task scheduler")
            q = mq(zmq.XREP, zmq.XREQ, zmq.PUB, 'intask', 'outtask')
            # q.setsockopt_out(zmq.HWM, hub.hwm)
            q.bind_in(hub.client_info['task'][1])
            q.setsockopt_in(zmq.IDENTITY, 'task')
            q.bind_out(hub.engine_info['task'])
            q.connect_mon(hub.monitor_url)
            q.daemon=True
            children.append(q)
        elif scheme == 'none':
            self.log.warn("task::using no Task scheduler")

        else:
            self.log.info("task::using Python %s Task scheduler"%scheme)
            sargs = (hub.client_info['task'][1], hub.engine_info['task'],
                                hub.monitor_url, hub.client_info['notification'])
            kwargs = dict(logname='scheduler', loglevel=self.log_level,
                            log_url = self.log_url, config=dict(self.config))
            q = Process(target=launch_scheduler, args=sargs, kwargs=kwargs)
            q.daemon=True
            children.append(q)

    
    def save_urls(self):
        """save the registration urls to files."""
        c = self.config
        
        sec_dir = self.profile_dir.security_dir
        cf = self.factory
        
        with open(os.path.join(sec_dir, 'ipcontroller-engine.url'), 'w') as f:
            f.write("%s://%s:%s"%(cf.engine_transport, cf.engine_ip, cf.regport))
        
        with open(os.path.join(sec_dir, 'ipcontroller-client.url'), 'w') as f:
            f.write("%s://%s:%s"%(cf.client_transport, cf.client_ip, cf.regport))
        
    
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
            self.log.removeHandler(self._log_handler)
            handler.root_topic = 'controller'
            handler.setLevel(self.log_level)
            self.log.addHandler(handler)
            self._log_handler = handler
    # #
    
    def initialize(self, argv=None):
        super(IPControllerApp, self).initialize(argv)
        self.forward_logging()
        self.init_hub()
        self.init_schedulers()
    
    def start(self):
        # Start the subprocesses:
        self.factory.start()
        child_procs = []
        for child in self.children:
            child.start()
            if isinstance(child, ProcessMonitoredQueue):
                child_procs.append(child.launcher)
            elif isinstance(child, Process):
                child_procs.append(child)
        if child_procs:
            signal_children(child_procs)

        self.write_pid_file(overwrite=True)

        try:
            self.factory.loop.start()
        except KeyboardInterrupt:
            self.log.critical("Interrupted, Exiting...\n")
            


def launch_new_instance():
    """Create and run the IPython controller"""
    app = IPControllerApp()
    app.initialize()
    app.start()


if __name__ == '__main__':
    launch_new_instance()
