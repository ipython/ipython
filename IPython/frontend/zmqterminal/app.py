from __future__ import print_function

import signal
import sys
import time

from IPython.frontend.terminal.ipapp import TerminalIPythonApp

from IPython.utils.traitlets import (
    Dict, List, Unicode, Int, CaselessStrEnum, CBool, Any
)
from IPython.zmq.ipkernel import (
    flags as ipkernel_flags,
    aliases as ipkernel_aliases,
    IPKernelApp
)
from IPython.zmq.session import Session
from IPython.zmq.zmqshell import ZMQInteractiveShell
from IPython.zmq.blockingkernelmanager import BlockingKernelManager
from IPython.zmq.ipkernel import (
    flags as ipkernel_flags,
    aliases as ipkernel_aliases,
    IPKernelApp
)
from IPython.frontend.zmqterminal.interactiveshell import ZMQTerminalInteractiveShell

#-----------------------------------------------------------------------------
# Network Constants
#-----------------------------------------------------------------------------

from IPython.utils.localinterfaces import LOCALHOST, LOCAL_IPS

#-----------------------------------------------------------------------------
# Flags and Aliases
#-----------------------------------------------------------------------------


flags = dict(ipkernel_flags)
frontend_flags = {
    'existing' : ({'ZMQTerminalIPythonApp' : {'existing' : True}},
            "Connect to an existing kernel."),
}
flags.update(frontend_flags)
# the flags that are specific to the frontend
# these must be scrubbed before being passed to the kernel,
# or it will raise an error on unrecognized flags
frontend_flags = frontend_flags.keys()

aliases = dict(ipkernel_aliases)

frontend_aliases = dict(
    hb = 'ZMQTerminalIPythonApp.hb_port',
    shell = 'ZMQTerminalIPythonApp.shell_port',
    iopub = 'ZMQTerminalIPythonApp.iopub_port',
    stdin = 'ZMQTerminalIPythonApp.stdin_port',
    ip = 'ZMQTerminalIPythonApp.ip',
)
aliases.update(frontend_aliases)
# also scrub aliases from the frontend
frontend_flags.extend(frontend_aliases.keys())

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class ZMQTerminalIPythonApp(TerminalIPythonApp):
    """Start a terminal frontend to the IPython zmq kernel."""
    
    kernel_argv = List(Unicode)
    flags = Dict(flags)
    aliases = Dict(aliases)
    classes = List([IPKernelApp, ZMQTerminalInteractiveShell])
    
    # connection info:
    ip = Unicode(LOCALHOST, config=True,
        help="""Set the kernel\'s IP address [default localhost].
        If the IP address is something other than localhost, then
        Consoles on other machines will be able to connect
        to the Kernel, so be careful!"""
    )
    pure = False
    hb_port = Int(0, config=True,
        help="set the heartbeat port [default: random]")
    shell_port = Int(0, config=True,
        help="set the shell (XREP) port [default: random]")
    iopub_port = Int(0, config=True,
        help="set the iopub (PUB) port [default: random]")
    stdin_port = Int(0, config=True,
        help="set the stdin (XREQ) port [default: random]")

    existing = CBool(False, config=True,
        help="Whether to connect to an already running Kernel.")

    # from qtconsoleapp:
    def parse_command_line(self, argv=None):
        super(ZMQTerminalIPythonApp, self).parse_command_line(argv)
        if argv is None:
            argv = sys.argv[1:]

        self.kernel_argv = list(argv) # copy
        # kernel should inherit default config file from frontend
        self.kernel_argv.append("--KernelApp.parent_appname='%s'"%self.name)
        # scrub frontend-specific flags
        for a in argv:
            
            if a.startswith('-'):
                key = a.lstrip('-').split('=')[0]
                if key in frontend_flags:
                    self.kernel_argv.remove(a)
    
    def init_kernel_manager(self):
        """init kernel manager (from qtconsole)"""
        # Don't let Qt or ZMQ swallow KeyboardInterupts.
        # signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Create a KernelManager and start a kernel.
        self.kernel_manager = BlockingKernelManager(
                                shell_address=(self.ip, self.shell_port),
                                sub_address=(self.ip, self.iopub_port),
                                stdin_address=(self.ip, self.stdin_port),
                                hb_address=(self.ip, self.hb_port),
                                config=self.config
        )
        # start the kernel
        if not self.existing:
            kwargs = dict(ip=self.ip, ipython=not self.pure)
            kwargs['extra_arguments'] = self.kernel_argv
            self.kernel_manager.start_kernel(**kwargs)
            # wait for kernel to start
            time.sleep(0.5)
        self.kernel_manager.start_channels()
        # relay sigint to kernel
        signal.signal(signal.SIGINT, self.handle_sigint)

    def init_shell(self):
        self.init_kernel_manager()
        self.shell = ZMQTerminalInteractiveShell.instance(config=self.config,
                        display_banner=False, profile_dir=self.profile_dir,
                        ipython_dir=self.ipython_dir, kernel_manager=self.kernel_manager)
    
    def handle_sigint(self, *args):
        # FIXME: this doesn't work, the kernel just dies every time
        self.shell.write('KeyboardInterrupt\n')
        self.kernel_manager.interrupt_kernel()
    
    def init_code(self):
        # no-op in the frontend, code gets run in the backend
        pass
        

def launch_new_instance():
    """Create and run a full blown IPython instance"""
    app = ZMQTerminalIPythonApp.instance()
    app.initialize()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

