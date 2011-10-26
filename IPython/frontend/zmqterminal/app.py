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
ipython console --pylab # start with pylab plotting mode
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
    """Start a terminal frontend to the IPython zmq kernel."""
    
    classes = List([IPKernelApp, ZMQTerminalInteractiveShell])
    flags = Dict(flags)
    aliases = Dict(aliases)
    def parse_command_line(self, argv=None):
        super(ZMQTerminalIPythonApp, self).parse_command_line(argv)
        IPythonMixinConsoleApp.parse_command_line(self,argv)
        self.swallow_args(frontend_aliases,frontend_flags,argv=argv)

    def init_shell(self):
        IPythonMixinConsoleApp.initialize(self)
        #self.init_kernel_manager()
        self.shell = ZMQTerminalInteractiveShell.instance(config=self.config,
                        display_banner=False, profile_dir=self.profile_dir,
                        ipython_dir=self.ipython_dir, kernel_manager=self.kernel_manager)

    def handle_sigint(self, *args):
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

