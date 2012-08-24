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

from IPython.frontend.terminal.ipapp import TerminalIPythonApp, frontend_flags as term_flags

from IPython.utils.traitlets import (
    Dict, List, Unicode, Int, CaselessStrEnum, CBool, Any
)
from IPython.utils.warn import warn,error

from IPython.zmq.ipkernel import IPKernelApp
from IPython.zmq.session import Session, default_secure
from IPython.zmq.zmqshell import ZMQInteractiveShell
from IPython.frontend.consoleapp import (
        IPythonConsoleApp, app_aliases, app_flags, aliases, app_aliases, flags
    )

from IPython.frontend.terminal.console.interactiveshell import ZMQTerminalInteractiveShell

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

# copy flags from mixin:
flags = dict(flags)
# start with mixin frontend flags:
frontend_flags = dict(app_flags)
# add TerminalIPApp flags:
frontend_flags.update(term_flags)
# disable quick startup, as it won't propagate to the kernel anyway
frontend_flags.pop('quick')
# update full dict with frontend flags:
flags.update(frontend_flags)

# copy flags from mixin
aliases = dict(aliases)
# start with mixin frontend flags
frontend_aliases = dict(app_aliases)
# load updated frontend flags into full dict
aliases.update(frontend_aliases)

# get flags&aliases into sets, and remove a couple that
# shouldn't be scrubbed from backend flags:
frontend_aliases = set(frontend_aliases.keys())
frontend_flags = set(frontend_flags.keys())


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class ZMQTerminalIPythonApp(TerminalIPythonApp, IPythonConsoleApp):
    name = "ipython-console"
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

    classes = [ZMQTerminalInteractiveShell] + IPythonConsoleApp.classes
    flags = Dict(flags)
    aliases = Dict(aliases)
    frontend_aliases = Any(frontend_aliases)
    frontend_flags = Any(frontend_flags)
    
    subcommands = Dict()

    def parse_command_line(self, argv=None):
        super(ZMQTerminalIPythonApp, self).parse_command_line(argv)
        self.build_kernel_argv(argv)

    def init_shell(self):
        IPythonConsoleApp.initialize(self)
        # relay sigint to kernel
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.shell = ZMQTerminalInteractiveShell.instance(config=self.config,
                        display_banner=False, profile_dir=self.profile_dir,
                        ipython_dir=self.ipython_dir, kernel_manager=self.kernel_manager)

    def init_gui_pylab(self):
        # no-op, because we don't want to import matplotlib in the frontend.
        pass

    def handle_sigint(self, *args):
        if self.shell._executing:
            if self.kernel_manager.has_kernel:
                # interrupt already gets passed to subprocess by signal handler.
                # Only if we prevent that should we need to explicitly call
                # interrupt_kernel, until which time, this would result in a 
                # double-interrupt:
                # self.kernel_manager.interrupt_kernel()
                pass
            else:
                self.shell.write_err('\n')
                error("Cannot interrupt kernels we didn't start.\n")
        else:
            # raise the KeyboardInterrupt if we aren't waiting for execution,
            # so that the interact loop advances, and prompt is redrawn, etc.
            raise KeyboardInterrupt
            

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

