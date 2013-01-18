""" An in-process kernel. """

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
from contextlib import contextmanager
import logging
import sys

# Local imports.
from IPython.core.interactiveshell import InteractiveShellABC
from IPython.inprocess.socket import DummySocket
from IPython.utils.jsonutil import json_clean
from IPython.utils.traitlets import Any, Enum, Instance, List, Type
from IPython.zmq.ipkernel import Kernel
from IPython.zmq.zmqshell import ZMQInteractiveShell

#-----------------------------------------------------------------------------
# Main kernel class
#-----------------------------------------------------------------------------

class InProcessKernel(Kernel):

    #-------------------------------------------------------------------------
    # InProcessKernel interface
    #-------------------------------------------------------------------------

    # The frontends connected to this kernel.
    frontends = List(
        Instance('IPython.inprocess.kernelmanager.InProcessKernelManager'))

    # The GUI environment that the kernel is running under. This need not be
    # specified for the normal operation for the kernel, but is required for
    # IPython's GUI support (including pylab). The default is 'inline' because
    # it is safe under all GUI toolkits.
    gui = Enum(('tk', 'gtk', 'wx', 'qt', 'qt4', 'inline'),
               default_value='inline')

    raw_input_str = Any()
    stdout = Any()
    stderr = Any()

    #-------------------------------------------------------------------------
    # Kernel interface
    #-------------------------------------------------------------------------

    shell_class = Type()
    shell_streams = List()
    control_stream = Any()
    iopub_socket = Instance(DummySocket, ())
    stdin_socket = Instance(DummySocket, ())

    def __init__(self, **traits):
        # When an InteractiveShell is instantiated by our base class, it binds
        # the current values of sys.stdout and sys.stderr.
        with self._redirected_io():
            super(InProcessKernel, self).__init__(**traits)

        self.iopub_socket.on_trait_change(self._io_dispatch, 'message_sent')
        self.shell.kernel = self

    def execute_request(self, stream, ident, parent):
        """ Override for temporary IO redirection. """
        with self._redirected_io():
            super(InProcessKernel, self).execute_request(stream, ident, parent)

    def start(self):
        """ Override registration of dispatchers for streams. """
        self.shell.exit_now = False

    def _abort_queue(self, stream):
        """ The in-process kernel doesn't abort requests. """
        pass

    def _raw_input(self, prompt, ident, parent):
        # Flush output before making the request.
        self.raw_input_str = None
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the input request.
        content = json_clean(dict(prompt=prompt))
        msg = self.session.msg(u'input_request', content, parent)
        for frontend in self.frontends:
            if frontend.session.session == parent['header']['session']:
                frontend.stdin_channel.call_handlers(msg)
                break
        else:
            logging.error('No frontend found for raw_input request')
            return str()

        # Await a response.
        while self.raw_input_str is None:
            frontend.stdin_channel.process_events()
        return self.raw_input_str

    #-------------------------------------------------------------------------
    # Protected interface
    #-------------------------------------------------------------------------

    @contextmanager
    def _redirected_io(self):
        """ Temporarily redirect IO to the kernel.
        """
        sys_stdout, sys_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.stdout, self.stderr
        yield
        sys.stdout, sys.stderr = sys_stdout, sys_stderr

    #------ Trait change handlers --------------------------------------------

    def _io_dispatch(self):
        """ Called when a message is sent to the IO socket.
        """
        ident, msg = self.session.recv(self.iopub_socket, copy=False)
        for frontend in self.frontends:
            frontend.iopub_channel.call_handlers(msg)
        
    #------ Trait initializers -----------------------------------------------

    def _log_default(self):
        return logging.getLogger(__name__)

    def _session_default(self):
        from IPython.zmq.session import Session
        return Session(config=self.config)

    def _shell_class_default(self):
        return InProcessInteractiveShell

    def _stdout_default(self):
        from IPython.zmq.iostream import OutStream
        return OutStream(self.session, self.iopub_socket, u'stdout')

    def _stderr_default(self):
        from IPython.zmq.iostream import OutStream
        return OutStream(self.session, self.iopub_socket, u'stderr')

#-----------------------------------------------------------------------------
# Interactive shell subclass
#-----------------------------------------------------------------------------

class InProcessInteractiveShell(ZMQInteractiveShell):

    kernel = Instance('IPython.inprocess.ipkernel.InProcessKernel')

    #-------------------------------------------------------------------------
    # InteractiveShell interface
    #-------------------------------------------------------------------------

    def enable_gui(self, gui=None):
        """ Enable GUI integration for the kernel.
        """
        from IPython.zmq.eventloops import enable_gui
        if not gui:
            gui = self.kernel.gui
        enable_gui(gui, kernel=self.kernel)

    def enable_pylab(self, gui=None, import_all=True, welcome_message=False):
        """ Activate pylab support at runtime.
        """
        if not gui:
            gui = self.kernel.gui
        super(InProcessInteractiveShell, self).enable_pylab(gui, import_all,
                                                            welcome_message)

InteractiveShellABC.register(InProcessInteractiveShell)
