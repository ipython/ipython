"""A kernel client for in-process kernels."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.kernel.channelsabc import (
    ShellChannelABC, IOPubChannelABC,
    HBChannelABC, StdInChannelABC,
)

from .socket import DummySocket

#-----------------------------------------------------------------------------
# Channel classes
#-----------------------------------------------------------------------------

class InProcessChannel(object):
    """Base class for in-process channels."""
    proxy_methods = []

    def __init__(self, client=None):
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

    def flush(self, timeout=1.0):
        pass

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

class InProcessIOPubChannel(InProcessChannel):
    """See `IPython.kernel.channels.IOPubChannel` for docstrings."""


class InProcessStdInChannel(InProcessChannel):
    """See `IPython.kernel.channels.StdInChannel` for docstrings."""



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
