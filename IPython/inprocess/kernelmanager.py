""" A kernel manager for in-process kernels. """

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Local imports.
from IPython.config.configurable import Configurable
from IPython.inprocess.socket import DummySocket
from IPython.utils.traitlets import Any, Instance, Type
from IPython.kernel import (
    ShellChannelABC, IOPubChannelABC,
    HBChannelABC, StdInChannelABC,
    KernelManagerABC
)

#-----------------------------------------------------------------------------
# Channel classes
#-----------------------------------------------------------------------------

class InProcessChannel(object):
    """Base class for in-process channels."""

    def __init__(self, manager):
        super(InProcessChannel, self).__init__()
        self.manager = manager
        self._is_alive = False

    #--------------------------------------------------------------------------
    # Channel interface
    #--------------------------------------------------------------------------

    def is_alive(self):
        return self._is_alive

    def start(self):
        self._is_alive = True

    def stop(self):
        self._is_alive = False

    def call_handlers(self, msg):
        """ This method is called in the main thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        """
        raise NotImplementedError('call_handlers must be defined in a subclass.')

    #--------------------------------------------------------------------------
    # InProcessChannel interface
    #--------------------------------------------------------------------------

    def call_handlers_later(self, *args, **kwds):
        """ Call the message handlers later.

        The default implementation just calls the handlers immediately, but this
        method exists so that GUI toolkits can defer calling the handlers until
        after the event loop has run, as expected by GUI frontends.
        """
        self.call_handlers(*args, **kwds)

    def process_events(self):
        """ Process any pending GUI events.

        This method will be never be called from a frontend without an event
        loop (e.g., a terminal frontend).
        """
        raise NotImplementedError


class InProcessShellChannel(InProcessChannel):
    """See `IPython.zmq.kernelmanager.ShellChannel` for docstrings."""

    # flag for whether execute requests should be allowed to call raw_input
    allow_stdin = True

    #--------------------------------------------------------------------------
    # ShellChannel interface
    #--------------------------------------------------------------------------

    def execute(self, code, silent=False, store_history=True,
                user_variables=[], user_expressions={}, allow_stdin=None):
        if allow_stdin is None:
            allow_stdin = self.allow_stdin
        content = dict(code=code, silent=silent, store_history=store_history,
                       user_variables=user_variables,
                       user_expressions=user_expressions,
                       allow_stdin=allow_stdin)
        msg = self.manager.session.msg('execute_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def complete(self, text, line, cursor_pos, block=None):
        content = dict(text=text, line=line, block=block, cursor_pos=cursor_pos)
        msg = self.manager.session.msg('complete_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def object_info(self, oname, detail_level=0):
        content = dict(oname=oname, detail_level=detail_level)
        msg = self.manager.session.msg('object_info_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def history(self, raw=True, output=False, hist_access_type='range', **kwds):
        content = dict(raw=raw, output=output,
                       hist_access_type=hist_access_type, **kwds)
        msg = self.manager.session.msg('history_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def shutdown(self, restart=False):
        # FIXME: What to do here?
        raise NotImplementedError('Cannot shutdown in-process kernel')

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _dispatch_to_kernel(self, msg):
        """ Send a message to the kernel and handle a reply.
        """
        kernel = self.manager.kernel
        if kernel is None:
            raise RuntimeError('Cannot send request. No kernel exists.')

        stream = DummySocket()
        self.manager.session.send(stream, msg)
        msg_parts = stream.recv_multipart()
        kernel.dispatch_shell(stream, msg_parts)

        idents, reply_msg = self.manager.session.recv(stream, copy=False)
        self.call_handlers_later(reply_msg)


class InProcessIOPubChannel(InProcessChannel):
    """See `IPython.zmq.kernelmanager.IOPubChannel` for docstrings."""

    def flush(self, timeout=1.0):
        pass


class InProcessStdInChannel(InProcessChannel):
    """See `IPython.zmq.kernelmanager.StdInChannel` for docstrings."""

    def input(self, string):
        kernel = self.manager.kernel
        if kernel is None:
            raise RuntimeError('Cannot send input reply. No kernel exists.')
        kernel.raw_input_str = string


class InProcessHBChannel(InProcessChannel):
    """See `IPython.zmq.kernelmanager.HBChannel` for docstrings."""

    time_to_dead = 3.0

    def __init__(self, *args, **kwds):
        super(InProcessHBChannel, self).__init__(*args, **kwds)
        self._pause = True

    def pause(self):
        self._pause = True

    def unpause(self):
        self._pause = False

    def is_beating(self):
        return not self._pause


#-----------------------------------------------------------------------------
# Main kernel manager class
#-----------------------------------------------------------------------------

class InProcessKernelManager(Configurable):
    """A manager for an in-process kernel.

    This class implements the interface of
    `IPython.kernel.kernelmanagerabc.KernelManagerABC` and allows
    (asynchronous) frontends to be used seamlessly with an in-process kernel.
    
    See `IPython.zmq.kernelmanager.KernelManager` for docstrings.
    """

    # The Session to use for building messages.
    session = Instance('IPython.zmq.session.Session')
    def _session_default(self):
        from IPython.zmq.session import Session
        return Session(config=self.config)

    # The kernel process with which the KernelManager is communicating.
    kernel = Instance('IPython.inprocess.ipkernel.InProcessKernel')

    # The classes to use for the various channels.
    shell_channel_class = Type(InProcessShellChannel)
    iopub_channel_class = Type(InProcessIOPubChannel)
    stdin_channel_class = Type(InProcessStdInChannel)
    hb_channel_class = Type(InProcessHBChannel)

    # Protected traits.
    _shell_channel = Any
    _iopub_channel = Any
    _stdin_channel = Any
    _hb_channel = Any

    #--------------------------------------------------------------------------
    # Channel management methods.
    #--------------------------------------------------------------------------

    def start_channels(self, shell=True, iopub=True, stdin=True, hb=True):
        if shell:
            self.shell_channel.start()
        if iopub:
            self.iopub_channel.start()
        if stdin:
            self.stdin_channel.start()
            self.shell_channel.allow_stdin = True
        else:
            self.shell_channel.allow_stdin = False
        if hb:
            self.hb_channel.start()

    def stop_channels(self):
        if self.shell_channel.is_alive():
            self.shell_channel.stop()
        if self.iopub_channel.is_alive():
            self.iopub_channel.stop()
        if self.stdin_channel.is_alive():
            self.stdin_channel.stop()
        if self.hb_channel.is_alive():
            self.hb_channel.stop()

    @property
    def channels_running(self):
        return (self.shell_channel.is_alive() or self.iopub_channel.is_alive() or
                self.stdin_channel.is_alive() or self.hb_channel.is_alive())

    @property
    def shell_channel(self):
        if self._shell_channel is None:
            self._shell_channel = self.shell_channel_class(self)
        return self._shell_channel

    @property
    def iopub_channel(self):
        if self._iopub_channel is None:
            self._iopub_channel = self.iopub_channel_class(self)
        return self._iopub_channel

    @property
    def stdin_channel(self):
        if self._stdin_channel is None:
            self._stdin_channel = self.stdin_channel_class(self)
        return self._stdin_channel

    @property
    def hb_channel(self):
        if self._hb_channel is None:
            self._hb_channel = self.hb_channel_class(self)
        return self._hb_channel

    #--------------------------------------------------------------------------
    # Kernel management methods:
    #--------------------------------------------------------------------------
    
    def start_kernel(self, **kwds):
        from IPython.inprocess.ipkernel import InProcessKernel
        self.kernel = InProcessKernel()
        self.kernel.frontends.append(self)

    def shutdown_kernel(self):
        self._kill_kernel()

    def restart_kernel(self, now=False, **kwds):
        self.shutdown_kernel()
        self.start_kernel(**kwds)

    @property
    def has_kernel(self):
        return self.kernel is not None

    def _kill_kernel(self):
        self.kernel.frontends.remove(self)
        self.kernel = None

    def interrupt_kernel(self):
        raise NotImplementedError("Cannot interrupt in-process kernel.")

    def signal_kernel(self, signum):
        raise NotImplementedError("Cannot signal in-process kernel.")

    @property
    def is_alive(self):
        return True


#-----------------------------------------------------------------------------
# ABC Registration
#-----------------------------------------------------------------------------

ShellChannelABC.register(InProcessShellChannel)
IOPubChannelABC.register(InProcessIOPubChannel)
HBChannelABC.register(InProcessHBChannel)
StdInChannelABC.register(InProcessStdInChannel)
KernelManagerABC.register(InProcessKernelManager)
