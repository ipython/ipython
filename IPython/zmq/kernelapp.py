"""An Application for launching a kernel

Authors
-------
* MinRK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
import atexit
import json
import os
import sys
import signal

# System library imports
import zmq
from zmq.eventloop import ioloop

# IPython imports
from IPython.core.ultratb import FormattedTB
from IPython.core.application import (
    BaseIPythonApplication, base_flags, base_aliases, catch_config_error
)
from IPython.utils import io
from IPython.utils.localinterfaces import LOCALHOST
from IPython.utils.path import filefind
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.traitlets import (
    Any, Instance, Dict, Unicode, Integer, Bool, CaselessStrEnum,
    DottedObjectName,
)
from IPython.utils.importstring import import_item
# local imports
from IPython.zmq.entry_point import write_connection_file
from IPython.zmq.heartbeat import Heartbeat
from IPython.zmq.parentpoller import ParentPollerUnix, ParentPollerWindows
from IPython.zmq.session import (
    Session, session_flags, session_aliases, default_secure,
)


#-----------------------------------------------------------------------------
# Flags and Aliases
#-----------------------------------------------------------------------------

kernel_aliases = dict(base_aliases)
kernel_aliases.update({
    'ip' : 'KernelApp.ip',
    'hb' : 'KernelApp.hb_port',
    'shell' : 'KernelApp.shell_port',
    'iopub' : 'KernelApp.iopub_port',
    'stdin' : 'KernelApp.stdin_port',
    'f' : 'KernelApp.connection_file',
    'parent': 'KernelApp.parent',
})
if sys.platform.startswith('win'):
    kernel_aliases['interrupt'] = 'KernelApp.interrupt'

kernel_flags = dict(base_flags)
kernel_flags.update({
    'no-stdout' : (
            {'KernelApp' : {'no_stdout' : True}},
            "redirect stdout to the null device"),
    'no-stderr' : (
            {'KernelApp' : {'no_stderr' : True}},
            "redirect stderr to the null device"),
})

# inherit flags&aliases for Sessions
kernel_aliases.update(session_aliases)
kernel_flags.update(session_flags)



#-----------------------------------------------------------------------------
# Application class for starting a Kernel
#-----------------------------------------------------------------------------

class KernelApp(BaseIPythonApplication):
    name='ipkernel'
    aliases = Dict(kernel_aliases)
    flags = Dict(kernel_flags)
    classes = [Session]
    # the kernel class, as an importstring
    kernel_class = DottedObjectName('IPython.zmq.ipkernel.Kernel')
    kernel = Any()
    poller = Any() # don't restrict this even though current pollers are all Threads
    heartbeat = Instance(Heartbeat)
    session = Instance('IPython.zmq.session.Session')
    ports = Dict()
    _full_connection_file = Unicode()
    
    # inherit config file name from parent:
    parent_appname = Unicode(config=True)
    def _parent_appname_changed(self, name, old, new):
        if self.config_file_specified:
            # it was manually specified, ignore
            return
        self.config_file_name = new.replace('-','_') + u'_config.py'
        # don't let this count as specifying the config file
        self.config_file_specified = False
        
    # connection info:
    transport = CaselessStrEnum(['tcp', 'ipc'], default_value='tcp', config=True)
    ip = Unicode(LOCALHOST, config=True,
        help="Set the IP or interface on which the kernel will listen.")
    hb_port = Integer(0, config=True, help="set the heartbeat port [default: random]")
    shell_port = Integer(0, config=True, help="set the shell (ROUTER) port [default: random]")
    iopub_port = Integer(0, config=True, help="set the iopub (PUB) port [default: random]")
    stdin_port = Integer(0, config=True, help="set the stdin (DEALER) port [default: random]")
    connection_file = Unicode('', config=True, 
    help="""JSON file in which to store connection info [default: kernel-<pid>.json]
    
    This file will contain the IP, ports, and authentication key needed to connect
    clients to this kernel. By default, this file will be created in the security-dir
    of the current profile, but can be specified by absolute path.
    """)

    # streams, etc.
    no_stdout = Bool(False, config=True, help="redirect stdout to the null device")
    no_stderr = Bool(False, config=True, help="redirect stderr to the null device")
    outstream_class = DottedObjectName('IPython.zmq.iostream.OutStream',
        config=True, help="The importstring for the OutStream factory")
    displayhook_class = DottedObjectName('IPython.zmq.displayhook.ZMQDisplayHook',
        config=True, help="The importstring for the DisplayHook factory")

    # polling
    parent = Integer(0, config=True,
        help="""kill this process if its parent dies.  On Windows, the argument
        specifies the HANDLE of the parent process, otherwise it is simply boolean.
        """)
    interrupt = Integer(0, config=True,
        help="""ONLY USED ON WINDOWS
        Interrupt this process when the parent is signalled.
        """)

    def init_crash_handler(self):
        # Install minimal exception handling
        sys.excepthook = FormattedTB(mode='Verbose', color_scheme='NoColor',
                                     ostream=sys.__stdout__)

    def init_poller(self):
        if sys.platform == 'win32':
            if self.interrupt or self.parent:
                self.poller = ParentPollerWindows(self.interrupt, self.parent)
        elif self.parent:
            self.poller = ParentPollerUnix()

    def _bind_socket(self, s, port):
        iface = '%s://%s' % (self.transport, self.ip)
        if port <= 0 and self.transport == 'tcp':
            port = s.bind_to_random_port(iface)
        else:
            c = ':' if self.transport == 'tcp' else '-'
            s.bind(iface + c + str(port))
        return port

    def load_connection_file(self):
        """load ip/port/hmac config from JSON connection file"""
        try:
            fname = filefind(self.connection_file, ['.', self.profile_dir.security_dir])
        except IOError:
            self.log.debug("Connection file not found: %s", self.connection_file)
            # This means I own it, so I will clean it up:
            atexit.register(self.cleanup_connection_file)
            return
        self.log.debug(u"Loading connection file %s", fname)
        with open(fname) as f:
            s = f.read()
        cfg = json.loads(s)
        self.transport = cfg.get('transport', self.transport)
        if self.ip == LOCALHOST and 'ip' in cfg:
            # not overridden by config or cl_args
            self.ip = cfg['ip']
        for channel in ('hb', 'shell', 'iopub', 'stdin'):
            name = channel + '_port'
            if getattr(self, name) == 0 and name in cfg:
                # not overridden by config or cl_args
                setattr(self, name, cfg[name])
        if 'key' in cfg:
            self.config.Session.key = str_to_bytes(cfg['key'])
    
    def write_connection_file(self):
        """write connection info to JSON file"""
        if os.path.basename(self.connection_file) == self.connection_file:
            cf = os.path.join(self.profile_dir.security_dir, self.connection_file)
        else:
            cf = self.connection_file
        write_connection_file(cf, ip=self.ip, key=self.session.key, transport=self.transport,
        shell_port=self.shell_port, stdin_port=self.stdin_port, hb_port=self.hb_port,
        iopub_port=self.iopub_port)
        
        self._full_connection_file = cf
    
    def cleanup_connection_file(self):
        cf = self._full_connection_file
        self.log.debug("cleaning up connection file: %r", cf)
        try:
            os.remove(cf)
        except (IOError, OSError):
            pass
        
        self.cleanup_ipc_files()
    
    def cleanup_ipc_files(self):
        """cleanup ipc files if we wrote them"""
        if self.transport != 'ipc':
            return
        for port in (self.shell_port, self.iopub_port, self.stdin_port, self.hb_port):
            ipcfile = "%s-%i" % (self.ip, port)
            try:
                os.remove(ipcfile)
            except (IOError, OSError):
                pass
    
    def init_connection_file(self):
        if not self.connection_file:
            self.connection_file = "kernel-%s.json"%os.getpid()
        try:
            self.load_connection_file()
        except Exception:
            self.log.error("Failed to load connection file: %r", self.connection_file, exc_info=True)
            self.exit(1)
    
    def init_sockets(self):
        # Create a context, a session, and the kernel sockets.
        self.log.info("Starting the kernel at pid: %i", os.getpid())
        context = zmq.Context.instance()
        # Uncomment this to try closing the context.
        # atexit.register(context.term)

        self.shell_socket = context.socket(zmq.ROUTER)
        self.shell_port = self._bind_socket(self.shell_socket, self.shell_port)
        self.log.debug("shell ROUTER Channel on port: %i"%self.shell_port)

        self.iopub_socket = context.socket(zmq.PUB)
        self.iopub_port = self._bind_socket(self.iopub_socket, self.iopub_port)
        self.log.debug("iopub PUB Channel on port: %i"%self.iopub_port)

        self.stdin_socket = context.socket(zmq.ROUTER)
        self.stdin_port = self._bind_socket(self.stdin_socket, self.stdin_port)
        self.log.debug("stdin ROUTER Channel on port: %i"%self.stdin_port)
    
    def init_heartbeat(self):
        """start the heart beating"""
        # heartbeat doesn't share context, because it mustn't be blocked
        # by the GIL, which is accessed by libzmq when freeing zero-copy messages
        hb_ctx = zmq.Context()
        self.heartbeat = Heartbeat(hb_ctx, (self.transport, self.ip, self.hb_port))
        self.hb_port = self.heartbeat.port
        self.log.debug("Heartbeat REP Channel on port: %i"%self.hb_port)
        self.heartbeat.start()

        # Helper to make it easier to connect to an existing kernel.
        # set log-level to critical, to make sure it is output
        self.log.critical("To connect another client to this kernel, use:")
    
    def log_connection_info(self):
        """display connection info, and store ports"""
        basename = os.path.basename(self.connection_file)
        if basename == self.connection_file or \
            os.path.dirname(self.connection_file) == self.profile_dir.security_dir:
            # use shortname
            tail = basename
            if self.profile != 'default':
                tail += " --profile %s" % self.profile
        else:
            tail = self.connection_file
        self.log.critical("--existing %s", tail)


        self.ports = dict(shell=self.shell_port, iopub=self.iopub_port,
                                stdin=self.stdin_port, hb=self.hb_port)

    def init_session(self):
        """create our session object"""
        default_secure(self.config)
        self.session = Session(config=self.config, username=u'kernel')

    def init_blackhole(self):
        """redirects stdout/stderr to devnull if necessary"""
        if self.no_stdout or self.no_stderr:
            blackhole = open(os.devnull, 'w')
            if self.no_stdout:
                sys.stdout = sys.__stdout__ = blackhole
            if self.no_stderr:
                sys.stderr = sys.__stderr__ = blackhole
    
    def init_io(self):
        """Redirect input streams and set a display hook."""
        if self.outstream_class:
            outstream_factory = import_item(str(self.outstream_class))
            sys.stdout = outstream_factory(self.session, self.iopub_socket, u'stdout')
            sys.stderr = outstream_factory(self.session, self.iopub_socket, u'stderr')
        if self.displayhook_class:
            displayhook_factory = import_item(str(self.displayhook_class))
            sys.displayhook = displayhook_factory(self.session, self.iopub_socket)

    def init_signal(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def init_kernel(self):
        """Create the Kernel object itself"""
        kernel_factory = import_item(str(self.kernel_class))
        self.kernel = kernel_factory(config=self.config, session=self.session,
                                shell_socket=self.shell_socket,
                                iopub_socket=self.iopub_socket,
                                stdin_socket=self.stdin_socket,
                                log=self.log
        )
        self.kernel.record_ports(self.ports)

    @catch_config_error
    def initialize(self, argv=None):
        super(KernelApp, self).initialize(argv)
        self.init_blackhole()
        self.init_connection_file()
        self.init_session()
        self.init_poller()
        self.init_sockets()
        self.init_heartbeat()
        # writing/displaying connection info must be *after* init_sockets/heartbeat
        self.log_connection_info()
        self.write_connection_file()
        self.init_io()
        self.init_signal()
        self.init_kernel()
        # flush stdout/stderr, so that anything written to these streams during
        # initialization do not get associated with the first execution request
        sys.stdout.flush()
        sys.stderr.flush()

    def start(self):
        if self.poller is not None:
            self.poller.start()
        self.kernel.start()
        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass

