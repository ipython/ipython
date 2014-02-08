""" A kernel client for in-process kernels. """

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# IPython imports
from IPython.kernel.channelsabc import (
    ShellChannelABC, IOPubChannelABC,
    HBChannelABC, StdInChannelABC,
)

# Local imports
from .socket import DummySocket

#-----------------------------------------------------------------------------
# Channel classes
#-----------------------------------------------------------------------------

class InProcessChannel(object):
    """Base class for in-process channels."""
    proxy_methods = []

    def __init__(self, client):
        super(InProcessChannel, self).__init__()
        self.client = client
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
    """See `IPython.kernel.channels.ShellChannel` for docstrings."""

    # flag for whether execute requests should be allowed to call raw_input
    allow_stdin = True
    proxy_methods = [
        'execute',
        'complete',
        'object_info',
        'history',
        'shutdown',
        'kernel_info',
    ]

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
        msg = self.client.session.msg('execute_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def complete(self, text, line, cursor_pos, block=None):
        content = dict(text=text, line=line, block=block, cursor_pos=cursor_pos)
        msg = self.client.session.msg('complete_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def object_info(self, oname, detail_level=0):
        content = dict(oname=oname, detail_level=detail_level)
        msg = self.client.session.msg('object_info_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def history(self, raw=True, output=False, hist_access_type='range', **kwds):
        content = dict(raw=raw, output=output,
                       hist_access_type=hist_access_type, **kwds)
        msg = self.client.session.msg('history_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def shutdown(self, restart=False):
        # FIXME: What to do here?
        raise NotImplementedError('Cannot shutdown in-process kernel')

    def kernel_info(self):
        """Request kernel info."""
        msg = self.client.session.msg('kernel_info_request')
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _dispatch_to_kernel(self, msg):
        """ Send a message to the kernel and handle a reply.
        """
        kernel = self.client.kernel
        if kernel is None:
            raise RuntimeError('Cannot send request. No kernel exists.')

        stream = DummySocket()
        self.client.session.send(stream, msg)
        msg_parts = stream.recv_multipart()
        kernel.dispatch_shell(stream, msg_parts)

        idents, reply_msg = self.client.session.recv(stream, copy=False)
        self.call_handlers_later(reply_msg)


class InProcessIOPubChannel(InProcessChannel):
    """See `IPython.kernel.channels.IOPubChannel` for docstrings."""

    def flush(self, timeout=1.0):
        pass


class InProcessStdInChannel(InProcessChannel):
    """See `IPython.kernel.channels.StdInChannel` for docstrings."""

    proxy_methods = ['input']

    def input(self, string):
        kernel = self.client.kernel
        if kernel is None:
            raise RuntimeError('Cannot send input reply. No kernel exists.')
        kernel.raw_input_str = string


class InProcessHBChannel(InProcessChannel):
    """See `IPython.kernel.channels.HBChannel` for docstrings."""

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
# ABC Registration
#-----------------------------------------------------------------------------

ShellChannelABC.register(InProcessShellChannel)
IOPubChannelABC.register(InProcessIOPubChannel)
HBChannelABC.register(InProcessHBChannel)
StdInChannelABC.register(InProcessStdInChannel)
