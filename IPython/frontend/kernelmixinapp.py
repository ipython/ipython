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
import json
import os
import signal
import sys
import uuid


# Local imports
from IPython.config.application import boolean_flag
from IPython.config.configurable import Configurable
from IPython.core.profiledir import ProfileDir
from IPython.lib.kernel import tunnel_to_kernel, find_connection_file
from IPython.zmq.blockingkernelmanager import BlockingKernelManager
from IPython.utils.path import filefind
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.traitlets import (
    Dict, List, Unicode, CUnicode, Int, CBool, Any
)
from IPython.zmq.ipkernel import (
    flags as ipkernel_flags,
    aliases as ipkernel_aliases,
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

flags = dict(ipkernel_flags)
app_flags = {
    'existing' : ({'IPythonMixinConsoleApp' : {'existing' : 'kernel*.json'}},
            "Connect to an existing kernel. If no argument specified, guess most recent"),
    'pure' : ({'IPythonMixinConsoleApp' : {'pure' : True}},
            "Use a pure Python kernel instead of an IPython kernel."),
    'plain' : ({'ConsoleWidget' : {'kind' : 'plain'}},
            "Disable rich text support."),
}
app_flags.update(boolean_flag(
    'confirm-exit', 'IPythonMixinConsoleApp.confirm_exit',
    """Set to display confirmation dialog on exit. You can always use 'exit' or 'quit',
       to force a direct exit without any confirmation.
    """,
    """Don't prompt the user when exiting. This will terminate the kernel
       if it is owned by the frontend, and leave it alive if it is external.
    """
))
flags.update(app_flags)

aliases = dict(ipkernel_aliases)

app_aliases = dict(
    hb = 'IPythonMixinConsoleApp.hb_port',
    shell = 'IPythonMixinConsoleApp.shell_port',
    iopub = 'IPythonMixinConsoleApp.iopub_port',
    stdin = 'IPythonMixinConsoleApp.stdin_port',
    ip = 'IPythonMixinConsoleApp.ip',
    existing = 'IPythonMixinConsoleApp.existing',
    f = 'IPythonMixinConsoleApp.connection_file',


    ssh = 'IPythonMixinConsoleApp.sshserver',
)
aliases.update(app_aliases)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# IPythonMixinConsole
#-----------------------------------------------------------------------------


class IPythonMixinConsoleApp(Configurable):
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

    classes = [IPKernelApp, ZMQInteractiveShell, ProfileDir, Session]
    flags = Dict(flags)
    aliases = Dict(aliases)
    kernel_manager_class = BlockingKernelManager

    kernel_argv = List(Unicode)

    # create requested profiles by default, if they don't exist:
    auto_create = CBool(True)
    # connection info:
    ip = Unicode(LOCALHOST, config=True,
        help="""Set the kernel\'s IP address [default localhost].
        If the IP address is something other than localhost, then
        Consoles on other machines will be able to connect
        to the Kernel, so be careful!"""
    )
    
    sshserver = Unicode('', config=True,
        help="""The SSH server to use to connect to the kernel.""")
    sshkey = Unicode('', config=True,
        help="""Path to the ssh key to use for logging in to the ssh server.""")
    
    hb_port = Int(0, config=True,
        help="set the heartbeat port [default: random]")
    shell_port = Int(0, config=True,
        help="set the shell (XREP) port [default: random]")
    iopub_port = Int(0, config=True,
        help="set the iopub (PUB) port [default: random]")
    stdin_port = Int(0, config=True,
        help="set the stdin (XREQ) port [default: random]")
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
    

    def parse_command_line(self, argv=None):
        super(PythonBaseConsoleApp, self).parse_command_line(argv)
        # make this stuff after this a function, in case the super stuff goes
        # away. Also, Min notes that this functionality should be moved to a
        # generic library of kernel stuff
        if argv is None:
            argv = sys.argv[1:]
        self.kernel_argv = list(argv) # copy
        # kernel should inherit default config file from frontend
        self.kernel_argv.append("--KernelApp.parent_appname='%s'"%self.name)
        # Scrub frontend-specific flags
        swallow_next = False
        was_flag = False
        # copy again, in case some aliases have the same name as a flag
        # argv = list(self.kernel_argv)
        for a in argv:
            if swallow_next:
                swallow_next = False
                # last arg was an alias, remove the next one
                # *unless* the last alias has a no-arg flag version, in which
                # case, don't swallow the next arg if it's also a flag:
                if not (was_flag and a.startswith('-')):
                    self.kernel_argv.remove(a)
                    continue
            if a.startswith('-'):
                split = a.lstrip('-').split('=')
                alias = split[0]
                if alias in qt_aliases:
                    self.kernel_argv.remove(a)
                    if len(split) == 1:
                        # alias passed with arg via space
                        swallow_next = True
                        # could have been a flag that matches an alias, e.g. `existing`
                        # in which case, we might not swallow the next arg
                        was_flag = alias in qt_flags
                elif alias in qt_flags:
                    # strip flag, but don't swallow next, as flags don't take args
                    self.kernel_argv.remove(a)
    
    def init_connection_file(self):
        """find the connection file, and load the info if found.
        
        The current working directory and the current profile's security
        directory will be searched for the file if it is not given by
        absolute path.
        
        When attempting to connect to an existing kernel and the `--existing`
        argument does not match an existing file, it will be interpreted as a
        fileglob, and the matching file in the current profile's security dir
        with the latest access time will be used.
        """
        if self.existing:
            try:
                cf = find_connection_file(self.existing)
            except Exception:
                self.log.critical("Could not find existing kernel connection file %s", self.existing)
                self.exit(1)
            self.log.info("Connecting to existing kernel: %s" % cf)
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
            s = f.read()
        cfg = json.loads(s)
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
    
    def init_ssh(self):
        """set up ssh tunnels, if needed."""
        if not self.sshserver and not self.sshkey:
            return
        
        if self.sshkey and not self.sshserver:
            # specifying just the key implies that we are connecting directly
            self.sshserver = self.ip
            self.ip = LOCALHOST
        
        # build connection dict for tunnels:
        info = dict(ip=self.ip,
                    shell_port=self.shell_port,
                    iopub_port=self.iopub_port,
                    stdin_port=self.stdin_port,
                    hb_port=self.hb_port
        )
        
        self.log.info("Forwarding connections to %s via %s"%(self.ip, self.sshserver))
        
        # tunnels return a new set of ports, which will be on localhost:
        self.ip = LOCALHOST
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
        return os.path.join(self.profile_dir.security_dir, 'kernel-%s.json' % uuid.uuid4())

    def init_kernel_manager(self):
        # Don't let Qt or ZMQ swallow KeyboardInterupts.
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sec = self.profile_dir.security_dir
        try:
            cf = filefind(self.connection_file, ['.', sec])
        except IOError:
            # file might not exist
            if self.connection_file == os.path.basename(self.connection_file):
                # just shortname, put it in security dir
                cf = os.path.join(sec, self.connection_file)
            else:
                cf = self.connection_file

        # Create a KernelManager and start a kernel.
        self.kernel_manager = self.kernel_manager_class(
                                ip=self.ip,
                                shell_port=self.shell_port,
                                iopub_port=self.iopub_port,
                                stdin_port=self.stdin_port,
                                hb_port=self.hb_port,
                                connection_file=cf,
                                config=self.config,
        )
        # start the kernel
        if not self.existing:
            kwargs = dict(ipython=not self.pure)
            kwargs['extra_arguments'] = self.kernel_argv
            self.kernel_manager.start_kernel(**kwargs)
        elif self.sshserver:
            # ssh, write new connection file
            self.kernel_manager.write_connection_file()
        self.kernel_manager.start_channels()


    def initialize(self, argv=None):
        super(IPythonMixinConsoleApp, self).initialize(argv)
        self.init_connection_file()
        default_secure(self.config)
        self.init_ssh()
        self.init_kernel_manager()
        self.init_colors()

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def main():
    raise NotImplementedError


if __name__ == '__main__':
    main()
