""" A minimal application base mixin for all ZMQ based IPython frontends.

This is not a complete console app, as subprocess will not be able to receive
input, there is no real readline support, among other limitations. This is a
refactoring of what used to be the IPython/frontend/qt/console/qtconsoleapp.py

Authors:

* Evan Patterson
* Min RK
* Erik Tollerud
* Fernando Perez
* Bussonnier Matthias
* Thomas Kluyver
* Paul Ivanov

"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# stdlib imports
import atexit
import json
import os
import shutil
import signal
import sys
import uuid


# Local imports
from IPython.config.application import boolean_flag
from IPython.config.configurable import Configurable
from IPython.core.profiledir import ProfileDir
from IPython.kernel.blockingkernelmanager import BlockingKernelManager
from IPython.kernel.kernelmanager import KernelManager
from IPython.kernel import tunnel_to_kernel, find_connection_file, swallow_argv
from IPython.utils.path import filefind
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.traitlets import (
    Dict, List, Unicode, CUnicode, Int, CBool, Any, CaselessStrEnum
)
from IPython.zmq.kernelapp import (
    kernel_flags,
    kernel_aliases,
    IPKernelApp
)
from IPython.zmq.session import Session, default_secure
from IPython.zmq.zmqshell import ZMQInteractiveShell

#-----------------------------------------------------------------------------
# Network Constants
#-----------------------------------------------------------------------------

from IPython.utils.localinterfaces import LOCALHOST, LOCAL_IPS

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Aliases and Flags
#-----------------------------------------------------------------------------

flags = dict(kernel_flags)

# the flags that are specific to the frontend
# these must be scrubbed before being passed to the kernel,
# or it will raise an error on unrecognized flags
app_flags = {
    'existing' : ({'IPythonConsoleApp' : {'existing' : 'kernel*.json'}},
            "Connect to an existing kernel. If no argument specified, guess most recent"),
}
app_flags.update(boolean_flag(
    'confirm-exit', 'IPythonConsoleApp.confirm_exit',
    """Set to display confirmation dialog on exit. You can always use 'exit' or 'quit',
       to force a direct exit without any confirmation.
    """,
    """Don't prompt the user when exiting. This will terminate the kernel
       if it is owned by the frontend, and leave it alive if it is external.
    """
))
flags.update(app_flags)

aliases = dict(kernel_aliases)

# also scrub aliases from the frontend
app_aliases = dict(
    ip = 'KernelManager.ip',
    transport = 'KernelManager.transport',
    hb = 'IPythonConsoleApp.hb_port',
    shell = 'IPythonConsoleApp.shell_port',
    iopub = 'IPythonConsoleApp.iopub_port',
    stdin = 'IPythonConsoleApp.stdin_port',
    existing = 'IPythonConsoleApp.existing',
    f = 'IPythonConsoleApp.connection_file',


    ssh = 'IPythonConsoleApp.sshserver',
)
aliases.update(app_aliases)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# IPythonConsole
#-----------------------------------------------------------------------------

classes = [IPKernelApp, ZMQInteractiveShell, KernelManager, ProfileDir, Session]

try:
    from IPython.zmq.pylab.backend_inline import InlineBackend
except ImportError:
    pass
else:
    classes.append(InlineBackend)

class IPythonConsoleApp(Configurable):
    name = 'ipython-console-mixin'
    default_config_file_name='ipython_config.py'

    description = """
        The IPython Mixin Console.
        
        This class contains the common portions of console client (QtConsole,
        ZMQ-based terminal console, etc).  It is not a full console, in that
        launched terminal subprocesses will not be able to accept input.
        
        The Console using this mixing supports various extra features beyond
        the single-process Terminal IPython shell, such as connecting to
        existing kernel, via:
        
            ipython <appname> --existing
        
        as well as tunnel via SSH
        
    """

    classes = classes
    flags = Dict(flags)
    aliases = Dict(aliases)
    kernel_manager_class = BlockingKernelManager

    kernel_argv = List(Unicode)
    # frontend flags&aliases to be stripped when building kernel_argv
    frontend_flags = Any(app_flags)
    frontend_aliases = Any(app_aliases)

    # create requested profiles by default, if they don't exist:
    auto_create = CBool(True)
    # connection info:
    
    sshserver = Unicode('', config=True,
        help="""The SSH server to use to connect to the kernel.""")
    sshkey = Unicode('', config=True,
        help="""Path to the ssh key to use for logging in to the ssh server.""")
    
    hb_port = Int(0, config=True,
        help="set the heartbeat port [default: random]")
    shell_port = Int(0, config=True,
        help="set the shell (ROUTER) port [default: random]")
    iopub_port = Int(0, config=True,
        help="set the iopub (PUB) port [default: random]")
    stdin_port = Int(0, config=True,
        help="set the stdin (DEALER) port [default: random]")
    connection_file = Unicode('', config=True,
        help="""JSON file in which to store connection info [default: kernel-<pid>.json]

        This file will contain the IP, ports, and authentication key needed to connect
        clients to this kernel. By default, this file will be created in the security-dir
        of the current profile, but can be specified by absolute path.
        """)
    def _connection_file_default(self):
        return 'kernel-%i.json' % os.getpid()

    existing = CUnicode('', config=True,
        help="""Connect to an already running kernel""")

    confirm_exit = CBool(True, config=True,
        help="""
        Set to display confirmation dialog on exit. You can always use 'exit' or 'quit',
        to force a direct exit without any confirmation.""",
    )


    def build_kernel_argv(self, argv=None):
        """build argv to be passed to kernel subprocess"""
        if argv is None:
            argv = sys.argv[1:]
        self.kernel_argv = swallow_argv(argv, self.frontend_aliases, self.frontend_flags)
        # kernel should inherit default config file from frontend
        self.kernel_argv.append("--KernelApp.parent_appname='%s'"%self.name)
    
    def init_connection_file(self):
        """find the connection file, and load the info if found.
        
        The current working directory and the current profile's security
        directory will be searched for the file if it is not given by
        absolute path.
        
        When attempting to connect to an existing kernel and the `--existing`
        argument does not match an existing file, it will be interpreted as a
        fileglob, and the matching file in the current profile's security dir
        with the latest access time will be used.
        
        After this method is called, self.connection_file contains the *full path*
        to the connection file, never just its name.
        """
        if self.existing:
            try:
                cf = find_connection_file(self.existing)
            except Exception:
                self.log.critical("Could not find existing kernel connection file %s", self.existing)
                self.exit(1)
            self.log.info("Connecting to existing kernel: %s" % cf)
            self.connection_file = cf
        else:
            # not existing, check if we are going to write the file
            # and ensure that self.connection_file is a full path, not just the shortname
            try:
                cf = find_connection_file(self.connection_file)
            except Exception:
                # file might not exist
                if self.connection_file == os.path.basename(self.connection_file):
                    # just shortname, put it in security dir
                    cf = os.path.join(self.profile_dir.security_dir, self.connection_file)
                else:
                    cf = self.connection_file
                self.connection_file = cf
        
        # should load_connection_file only be used for existing?
        # as it is now, this allows reusing ports if an existing
        # file is requested
        try:
            self.load_connection_file()
        except Exception:
            self.log.error("Failed to load connection file: %r", self.connection_file, exc_info=True)
            self.exit(1)
    
    def load_connection_file(self):
        """load ip/port/hmac config from JSON connection file"""
        # this is identical to KernelApp.load_connection_file
        # perhaps it can be centralized somewhere?
        try:
            fname = filefind(self.connection_file, ['.', self.profile_dir.security_dir])
        except IOError:
            self.log.debug("Connection File not found: %s", self.connection_file)
            return
        self.log.debug(u"Loading connection file %s", fname)
        with open(fname) as f:
            cfg = json.load(f)
        
        self.config.KernelManager.transport = cfg.get('transport', 'tcp')
        self.config.KernelManager.ip = cfg.get('ip', LOCALHOST)
        
        for channel in ('hb', 'shell', 'iopub', 'stdin'):
            name = channel + '_port'
            if getattr(self, name) == 0 and name in cfg:
                # not overridden by config or cl_args
                setattr(self, name, cfg[name])
        if 'key' in cfg:
            self.config.Session.key = str_to_bytes(cfg['key'])
    
    def init_ssh(self):
        """set up ssh tunnels, if needed."""
        if not self.existing or (not self.sshserver and not self.sshkey):
            return
        
        self.load_connection_file()
        
        transport = self.config.KernelManager.transport
        ip = self.config.KernelManager.ip
        
        if transport != 'tcp':
            self.log.error("Can only use ssh tunnels with TCP sockets, not %s", transport)
            sys.exit(-1)
        
        if self.sshkey and not self.sshserver:
            # specifying just the key implies that we are connecting directly
            self.sshserver = ip
            ip = LOCALHOST
        
        # build connection dict for tunnels:
        info = dict(ip=ip,
                    shell_port=self.shell_port,
                    iopub_port=self.iopub_port,
                    stdin_port=self.stdin_port,
                    hb_port=self.hb_port
        )
        
        self.log.info("Forwarding connections to %s via %s"%(ip, self.sshserver))
        
        # tunnels return a new set of ports, which will be on localhost:
        self.config.KernelManager.ip = LOCALHOST
        try:
            newports = tunnel_to_kernel(info, self.sshserver, self.sshkey)
        except:
            # even catch KeyboardInterrupt
            self.log.error("Could not setup tunnels", exc_info=True)
            self.exit(1)
        
        self.shell_port, self.iopub_port, self.stdin_port, self.hb_port = newports
        
        cf = self.connection_file
        base,ext = os.path.splitext(cf)
        base = os.path.basename(base)
        self.connection_file = os.path.basename(base)+'-ssh'+ext
        self.log.critical("To connect another client via this tunnel, use:")
        self.log.critical("--existing %s" % self.connection_file)
    
    def _new_connection_file(self):
        cf = ''
        while not cf:
            # we don't need a 128b id to distinguish kernels, use more readable
            # 48b node segment (12 hex chars).  Users running more than 32k simultaneous
            # kernels can subclass.
            ident = str(uuid.uuid4()).split('-')[-1]
            cf = os.path.join(self.profile_dir.security_dir, 'kernel-%s.json' % ident)
            # only keep if it's actually new.  Protect against unlikely collision
            # in 48b random search space
            cf = cf if not os.path.exists(cf) else ''
        return cf

    def init_kernel_manager(self):
        # Don't let Qt or ZMQ swallow KeyboardInterupts.
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Create a KernelManager and start a kernel.
        self.kernel_manager = self.kernel_manager_class(
                                shell_port=self.shell_port,
                                iopub_port=self.iopub_port,
                                stdin_port=self.stdin_port,
                                hb_port=self.hb_port,
                                connection_file=self.connection_file,
                                config=self.config,
        )
        # start the kernel
        if not self.existing:
            self.kernel_manager.start_kernel(extra_arguments=self.kernel_argv)
            atexit.register(self.kernel_manager.cleanup_ipc_files)
        elif self.sshserver:
            # ssh, write new connection file
            self.kernel_manager.write_connection_file()
        atexit.register(self.kernel_manager.cleanup_connection_file)
        self.kernel_manager.start_channels()


    def initialize(self, argv=None):
        """
        Classes which mix this class in should call:
               IPythonConsoleApp.initialize(self,argv)
        """
        self.init_connection_file()
        default_secure(self.config)
        self.init_ssh()
        self.init_kernel_manager()

