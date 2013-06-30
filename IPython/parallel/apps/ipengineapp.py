#!/usr/bin/env python
# encoding: utf-8
"""
The IPython engine application

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

import json
import os
import sys
import time

import zmq
from zmq.eventloop import ioloop

from IPython.core.profiledir import ProfileDir
from IPython.parallel.apps.baseapp import (
    BaseParallelApplication,
    base_aliases,
    base_flags,
    catch_config_error,
)
from IPython.kernel.zmq.log import EnginePUBHandler
from IPython.kernel.zmq.ipkernel import Kernel
from IPython.kernel.zmq.kernelapp import IPKernelApp
from IPython.kernel.zmq.session import (
    Session, session_aliases, session_flags
)
from IPython.kernel.zmq.zmqshell import ZMQInteractiveShell

from IPython.config.configurable import Configurable

from IPython.parallel.engine.engine import EngineFactory
from IPython.parallel.util import disambiguate_ip_address

from IPython.utils.importstring import import_item
from IPython.utils.py3compat import cast_bytes
from IPython.utils.traitlets import Bool, Unicode, Dict, List, Float, Instance


#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------

#: The default config file name for this application
default_config_file_name = u'ipengine_config.py'

_description = """Start an IPython engine for parallel computing.

IPython engines run in parallel and perform computations on behalf of a client
and controller. A controller needs to be started before the engines. The
engine can be configured using command line options or using a cluster
directory. Cluster directories contain config, log and security files and are
usually located in your ipython directory and named as "profile_name".
See the `profile` and `profile-dir` options for details.
"""

_examples = """
ipengine --ip=192.168.0.1 --port=1000     # connect to hub at ip and port
ipengine --log-to-file --log-level=DEBUG  # log to a file with DEBUG verbosity
"""

#-----------------------------------------------------------------------------
# MPI configuration
#-----------------------------------------------------------------------------

mpi4py_init = """from mpi4py import MPI as mpi
mpi.size = mpi.COMM_WORLD.Get_size()
mpi.rank = mpi.COMM_WORLD.Get_rank()
"""


pytrilinos_init = """from PyTrilinos import Epetra
class SimpleStruct:
pass
mpi = SimpleStruct()
mpi.rank = 0
mpi.size = 0
"""

class MPI(Configurable):
    """Configurable for MPI initialization"""
    use = Unicode('', config=True,
        help='How to enable MPI (mpi4py, pytrilinos, or empty string to disable).'
        )

    def _use_changed(self, name, old, new):
        # load default init script if it's not set
        if not self.init_script:
            self.init_script = self.default_inits.get(new, '')

    init_script = Unicode('', config=True,
        help="Initialization code for MPI")

    default_inits = Dict({'mpi4py' : mpi4py_init, 'pytrilinos':pytrilinos_init},
        config=True)


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------
aliases = dict(
    file = 'IPEngineApp.url_file',
    c = 'IPEngineApp.startup_command',
    s = 'IPEngineApp.startup_script',

    url = 'EngineFactory.url',
    ssh = 'EngineFactory.sshserver',
    sshkey = 'EngineFactory.sshkey',
    ip = 'EngineFactory.ip',
    transport = 'EngineFactory.transport',
    port = 'EngineFactory.regport',
    location = 'EngineFactory.location',

    timeout = 'EngineFactory.timeout',

    mpi = 'MPI.use',

)
aliases.update(base_aliases)
aliases.update(session_aliases)
flags = {}
flags.update(base_flags)
flags.update(session_flags)

class IPEngineApp(BaseParallelApplication):

    name = 'ipengine'
    description = _description
    examples = _examples
    config_file_name = Unicode(default_config_file_name)
    classes = List([ZMQInteractiveShell, ProfileDir, Session, EngineFactory, Kernel, MPI])

    startup_script = Unicode(u'', config=True,
        help='specify a script to be run at startup')
    startup_command = Unicode('', config=True,
            help='specify a command to be run at startup')

    url_file = Unicode(u'', config=True,
        help="""The full location of the file containing the connection information for
        the controller. If this is not given, the file must be in the
        security directory of the cluster directory.  This location is
        resolved using the `profile` or `profile_dir` options.""",
        )
    wait_for_url_file = Float(5, config=True,
        help="""The maximum number of seconds to wait for url_file to exist.
        This is useful for batch-systems and shared-filesystems where the
        controller and engine are started at the same time and it
        may take a moment for the controller to write the connector files.""")

    url_file_name = Unicode(u'ipcontroller-engine.json', config=True)

    def _cluster_id_changed(self, name, old, new):
        if new:
            base = 'ipcontroller-%s' % new
        else:
            base = 'ipcontroller'
        self.url_file_name = "%s-engine.json" % base

    log_url = Unicode('', config=True,
        help="""The URL for the iploggerapp instance, for forwarding
        logging to a central location.""")
    
    # an IPKernelApp instance, used to setup listening for shell frontends
    kernel_app = Instance(IPKernelApp)

    aliases = Dict(aliases)
    flags = Dict(flags)
    
    @property
    def kernel(self):
        """allow access to the Kernel object, so I look like IPKernelApp"""
        return self.engine.kernel

    def find_url_file(self):
        """Set the url file.

        Here we don't try to actually see if it exists for is valid as that
        is hadled by the connection logic.
        """
        config = self.config
        # Find the actual controller key file
        if not self.url_file:
            self.url_file = os.path.join(
                self.profile_dir.security_dir,
                self.url_file_name
            )
    
    def load_connector_file(self):
        """load config from a JSON connector file,
        at a *lower* priority than command-line/config files.
        """
        
        self.log.info("Loading url_file %r", self.url_file)
        config = self.config
        
        with open(self.url_file) as f:
            d = json.loads(f.read())
        
        # allow hand-override of location for disambiguation
        # and ssh-server
        try:
            config.EngineFactory.location
        except AttributeError:
            config.EngineFactory.location = d['location']
        
        try:
            config.EngineFactory.sshserver
        except AttributeError:
            config.EngineFactory.sshserver = d.get('ssh')
        
        location = config.EngineFactory.location
        
        proto, ip = d['interface'].split('://')
        ip = disambiguate_ip_address(ip, location)
        d['interface'] = '%s://%s' % (proto, ip)
        
        # DO NOT allow override of basic URLs, serialization, or exec_key
        # JSON file takes top priority there
        config.Session.key = cast_bytes(d['exec_key'])
        
        config.EngineFactory.url = d['interface'] + ':%i' % d['registration']
        
        config.Session.packer = d['pack']
        config.Session.unpacker = d['unpack']
        
        self.log.debug("Config changed:")
        self.log.debug("%r", config)
        self.connection_info = d
    
    def bind_kernel(self, **kwargs):
        """Promote engine to listening kernel, accessible to frontends."""
        if self.kernel_app is not None:
            return
        
        self.log.info("Opening ports for direct connections as an IPython kernel")
        
        kernel = self.kernel
        
        kwargs.setdefault('config', self.config)
        kwargs.setdefault('log', self.log)
        kwargs.setdefault('profile_dir', self.profile_dir)
        kwargs.setdefault('session', self.engine.session)
        
        app = self.kernel_app = IPKernelApp(**kwargs)
        
        # allow IPKernelApp.instance():
        IPKernelApp._instance = app
        
        app.init_connection_file()
        # relevant contents of init_sockets:
        
        app.shell_port = app._bind_socket(kernel.shell_streams[0], app.shell_port)
        app.log.debug("shell ROUTER Channel on port: %i", app.shell_port)
        
        app.iopub_port = app._bind_socket(kernel.iopub_socket, app.iopub_port)
        app.log.debug("iopub PUB Channel on port: %i", app.iopub_port)
        
        kernel.stdin_socket = self.engine.context.socket(zmq.ROUTER)
        app.stdin_port = app._bind_socket(kernel.stdin_socket, app.stdin_port)
        app.log.debug("stdin ROUTER Channel on port: %i", app.stdin_port)
        
        # start the heartbeat, and log connection info:
        
        app.init_heartbeat()
        
        app.log_connection_info()
        app.write_connection_file()
        
    
    def init_engine(self):
        # This is the working dir by now.
        sys.path.insert(0, '')
        config = self.config
        # print config
        self.find_url_file()
        
        # was the url manually specified?
        keys = set(self.config.EngineFactory.keys())
        keys = keys.union(set(self.config.RegistrationFactory.keys()))
        
        if keys.intersection(set(['ip', 'url', 'port'])):
            # Connection info was specified, don't wait for the file
            url_specified = True
            self.wait_for_url_file = 0
        else:
            url_specified = False

        if self.wait_for_url_file and not os.path.exists(self.url_file):
            self.log.warn("url_file %r not found", self.url_file)
            self.log.warn("Waiting up to %.1f seconds for it to arrive.", self.wait_for_url_file)
            tic = time.time()
            while not os.path.exists(self.url_file) and (time.time()-tic < self.wait_for_url_file):
                # wait for url_file to exist, or until time limit
                time.sleep(0.1)
            
        if os.path.exists(self.url_file):
            self.load_connector_file()
        elif not url_specified:
            self.log.fatal("Fatal: url file never arrived: %s", self.url_file)
            self.exit(1)
        
        
        try:
            exec_lines = config.IPKernelApp.exec_lines
        except AttributeError:
            try:
                exec_lines = config.InteractiveShellApp.exec_lines
            except AttributeError:
                exec_lines = config.IPKernelApp.exec_lines = []
        try:
            exec_files = config.IPKernelApp.exec_files
        except AttributeError:
            try:
                exec_files = config.InteractiveShellApp.exec_files
            except AttributeError:
                exec_files = config.IPKernelApp.exec_files = []
        
        if self.startup_script:
            exec_files.append(self.startup_script)
        if self.startup_command:
            exec_lines.append(self.startup_command)

        # Create the underlying shell class and Engine
        # shell_class = import_item(self.master_config.Global.shell_class)
        # print self.config
        try:
            self.engine = EngineFactory(config=config, log=self.log,
                            connection_info=self.connection_info,
                        )
        except:
            self.log.error("Couldn't start the Engine", exc_info=True)
            self.exit(1)
    
    def forward_logging(self):
        if self.log_url:
            self.log.info("Forwarding logging to %s", self.log_url)
            context = self.engine.context
            lsock = context.socket(zmq.PUB)
            lsock.connect(self.log_url)
            handler = EnginePUBHandler(self.engine, lsock)
            handler.setLevel(self.log_level)
            self.log.addHandler(handler)
    
    def init_mpi(self):
        global mpi
        self.mpi = MPI(parent=self)

        mpi_import_statement = self.mpi.init_script
        if mpi_import_statement:
            try:
                self.log.info("Initializing MPI:")
                self.log.info(mpi_import_statement)
                exec mpi_import_statement in globals()
            except:
                mpi = None
        else:
            mpi = None

    @catch_config_error
    def initialize(self, argv=None):
        super(IPEngineApp, self).initialize(argv)
        self.init_mpi()
        self.init_engine()
        self.forward_logging()
    
    def start(self):
        self.engine.start()
        try:
            self.engine.loop.start()
        except KeyboardInterrupt:
            self.log.critical("Engine Interrupted, shutting down...\n")


def launch_new_instance():
    """Create and run the IPython engine"""
    app = IPEngineApp.instance()
    app.initialize()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

