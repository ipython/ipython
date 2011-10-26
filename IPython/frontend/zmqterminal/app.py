""" A minimal application using the ZMQ-based terminal IPython frontend.

This is not a complete console app, as subprocess will not be able to receive
input, there is no real readline support, among other limitations.

Authors:

* Min RK
* Paul Ivanov

"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import signal
import sys
import time

from IPython.frontend.terminal.ipapp import TerminalIPythonApp

from IPython.utils.traitlets import (
    Dict, List, Unicode, Int, CaselessStrEnum, CBool, Any
)
from IPython.zmq.ipkernel import IPKernelApp
from IPython.zmq.session import Session, default_secure
from IPython.zmq.zmqshell import ZMQInteractiveShell
from IPython.frontend.kernelmixinapp import (
        IPythonMixinConsoleApp, app_aliases, app_flags
    )

from IPython.frontend.zmqterminal.interactiveshell import ZMQTerminalInteractiveShell

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

_examples = """
ipython console # start the ZMQ-based console
ipython console --existing # connect to an existing ipython session
"""

#-----------------------------------------------------------------------------
# Flags and Aliases
#-----------------------------------------------------------------------------

# XXX: the app_flags should really be flags from the mixin
flags = dict(app_flags)
frontend_flags = { }
flags.update(frontend_flags)

frontend_flags = frontend_flags.keys()

aliases = dict(app_aliases)

frontend_aliases = dict()

aliases.update(frontend_aliases)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class ZMQTerminalIPythonApp(TerminalIPythonApp, IPythonMixinConsoleApp):
    name = "ipython console"
    """Start a terminal frontend to the IPython zmq kernel."""

    description = """
        The IPython terminal-based Console.

        This launches a Console application inside a terminal.

        The Console supports various extra features beyond the traditional
        single-process Terminal IPython shell, such as connecting to an
        existing ipython session, via:

            ipython console --existing

        where the previous session could have been created by another ipython
        console, an ipython qtconsole, or by opening an ipython notebook.

    """
    examples = _examples

    classes = List([IPKernelApp, ZMQTerminalInteractiveShell])
    flags = Dict(flags)
    aliases = Dict(aliases)
    subcommands = Dict()
    def parse_command_line(self, argv=None):
        super(ZMQTerminalIPythonApp, self).parse_command_line(argv)
        IPythonMixinConsoleApp.parse_command_line(self,argv)
        self.swallow_args(frontend_aliases,frontend_flags,argv=argv)

    def init_shell(self):
        IPythonMixinConsoleApp.initialize(self)
        # relay sigint to kernel
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.shell = ZMQTerminalInteractiveShell.instance(config=self.config,
                        display_banner=False, profile_dir=self.profile_dir,
                        ipython_dir=self.ipython_dir, kernel_manager=self.kernel_manager)

    def handle_sigint(self, *args):
        self.shell.write('KeyboardInterrupt\n')
        if self.kernel_manager.has_kernel:
            self.kernel_manager.interrupt_kernel()
        else:
            print 'Kernel process is either remote or unspecified.',
            print 'Cannot interrupt.'

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

