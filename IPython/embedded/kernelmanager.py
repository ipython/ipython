""" A kernel manager for embedded (in-process) kernels. """

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
from IPython.config.loader import Config
from IPython.utils.traitlets import HasTraits, Any, Instance, Type

#-----------------------------------------------------------------------------
# Channel classes
#-----------------------------------------------------------------------------

class EmbeddedChannel(object):
    """ Base class for embedded channels.
    """

    def __init__(self, manager):
        super(EmbeddedChannel, self).__init__()
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
    # EmbeddedChannel interface
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


class ShellEmbeddedChannel(EmbeddedChannel):
    """The DEALER channel for issues request/replies to the kernel.
    """

    # flag for whether execute requests should be allowed to call raw_input
    allow_stdin = True

    def execute(self, code, silent=False, store_history=True,
                user_variables=[], user_expressions={}, allow_stdin=None):
        """Execute code in the kernel.

        Parameters
        ----------
        code : str
            A string of Python code.

        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible, and
            will force store_history to be False.

        store_history : bool, optional (default True)
            If set, the kernel will store command history.  This is forced
            to be False if silent is True.

        user_variables : list, optional
            A list of variable names to pull from the user's namespace.  They
            will come back as a dict with these names as keys and their
            :func:`repr` as values.

        user_expressions : dict, optional
            A dict mapping names to expressions to be evaluated in the user's
            dict. The expression values are returned as strings formatted using
            :func:`repr`.

        allow_stdin : bool, optional (default self.allow_stdin)
            Flag for whether the kernel can send stdin requests to frontends.

            Some frontends (e.g. the Notebook) do not support stdin requests. 
            If raw_input is called from code executed from such a frontend, a
            StdinNotImplementedError will be raised.

        Returns
        -------
        The msg_id of the message sent.
        """
        raise NotImplementedError

    def complete(self, text, line, cursor_pos, block=None):
        """Tab complete text in the kernel's namespace.

        Parameters
        ----------
        text : str
            The text to complete.
        line : str
            The full line of text that is the surrounding context for the
            text to complete.
        cursor_pos : int
            The position of the cursor in the line where the completion was
            requested.
        block : str, optional
            The full block of code in which the completion is being requested.

        Returns
        -------
        The msg_id of the message sent.
        """
        raise NotImplementedError

    def object_info(self, oname, detail_level=0):
        """Get metadata information about an object.

        Parameters
        ----------
        oname : str
            A string specifying the object name.
        detail_level : int, optional
            The level of detail for the introspection (0-2)

        Returns
        -------
        The msg_id of the message sent.
        """
        raise NotImplementedError

    def history(self, raw=True, output=False, hist_access_type='range', **kwds):
        """Get entries from the history list.

        Parameters
        ----------
        raw : bool
            If True, return the raw input.
        output : bool
            If True, then return the output as well.
        hist_access_type : str
            'range' (fill in session, start and stop params), 'tail' (fill in n)
             or 'search' (fill in pattern param).

        session : int
            For a range request, the session from which to get lines. Session
            numbers are positive integers; negative ones count back from the
            current session.
        start : int
            The first line number of a history range.
        stop : int
            The final (excluded) line number of a history range.

        n : int
            The number of lines of history to get for a tail request.

        pattern : str
            The glob-syntax pattern for a search request.

        Returns
        -------
        The msg_id of the message sent.
        """
        raise NotImplementedError

    def shutdown(self, restart=False):
        """ Request an immediate kernel shutdown.

        A dummy method for the embedded kernel.
        """
        # FIXME: What to do here?
        raise NotImplementedError('Shutdown not supported for embedded kernel')


class SubEmbeddedChannel(EmbeddedChannel):
    """The SUB channel which listens for messages that the kernel publishes. 
    """

    def flush(self, timeout=1.0):
        """ Immediately processes all pending messages on the SUB channel.

        A dummy method for the embedded kernel.
        """
        pass


class StdInEmbeddedChannel(EmbeddedChannel):
    """ A reply channel to handle raw_input requests that the kernel makes. """

    def input(self, string):
        """ Send a string of raw input to the kernel. 
        """
        raise NotImplementedError


class HBEmbeddedChannel(EmbeddedChannel):
    """ A dummy heartbeat channel. """

    time_to_dead = 3.0

    def __init__(self, *args, **kwds):
        super(HBEmbeddedChannel, self).__init__(*args, **kwds)
        self._pause = True

    def pause(self):
        """ Pause the heartbeat. """
        self._pause = True

    def unpause(self):
        """ Unpause the heartbeat. """
        self._pause = False

    def is_beating(self):
        """ Is the heartbeat running and responsive (and not paused). """
        return not self._pause


#-----------------------------------------------------------------------------
# Main kernel manager class
#-----------------------------------------------------------------------------

class EmbeddedKernelManager(HasTraits):
    """ A manager for an embedded kernel.

    This class implements most of the interface of
    ``IPython.zmq.kernelmanager.KernelManager`` and allows (asynchronous)
    frontends to be used seamlessly with an in-process kernel.
    """
    # Config object for passing to child configurables
    config = Instance(Config)

    # The Session to use for building messages.
    session = Instance('IPython.zmq.session.Session')
    def _session_default(self):
        from IPython.zmq.session import Session
        return Session(config=self.config)

    # The kernel process with which the KernelManager is communicating.
    kernel = Instance('IPython.embedded.ipkernel.EmbeddedKernel')

    # The classes to use for the various channels.
    shell_channel_class = Type(ShellEmbeddedChannel)
    sub_channel_class = Type(SubEmbeddedChannel)
    stdin_channel_class = Type(StdInEmbeddedChannel)
    hb_channel_class = Type(HBEmbeddedChannel)

    # Protected traits.
    _shell_channel = Any
    _sub_channel = Any
    _stdin_channel = Any
    _hb_channel = Any

    #--------------------------------------------------------------------------
    # Channel management methods:
    #--------------------------------------------------------------------------

    def start_channels(self, shell=True, sub=True, stdin=True, hb=True):
        """ Starts the channels for this kernel.
        """
        if shell:
            self.shell_channel.start()
        if sub:
            self.sub_channel.start()
        if stdin:
            self.stdin_channel.start()
            self.shell_channel.allow_stdin = True
        else:
            self.shell_channel.allow_stdin = False
        if hb:
            self.hb_channel.start()

    def stop_channels(self):
        """ Stops all the running channels for this kernel.
        """
        if self.shell_channel.is_alive():
            self.shell_channel.stop()
        if self.sub_channel.is_alive():
            self.sub_channel.stop()
        if self.stdin_channel.is_alive():
            self.stdin_channel.stop()
        if self.hb_channel.is_alive():
            self.hb_channel.stop()

    @property
    def channels_running(self):
        """ Are any of the channels created and running? """
        return (self.shell_channel.is_alive() or self.sub_channel.is_alive() or
                self.stdin_channel.is_alive() or self.hb_channel.is_alive())

    #--------------------------------------------------------------------------
    # Kernel management methods:
    #--------------------------------------------------------------------------
    
    def start_kernel(self, **kwds):
        """ Starts a kernel process and configures the manager to use it.
        """
        from IPython.embedded.ipkernel import EmbeddedKernel
        self.kernel = EmbeddedKernel()
        self.kernel.frontends.append(self)

    def shutdown_kernel(self):
        """ Attempts to the stop the kernel process cleanly. If the kernel
        cannot be stopped and the kernel is local, it is killed.
        """
        self.kill_kernel()

    def restart_kernel(self, now=False, **kwds):
        """ Restarts a kernel with the arguments that were used to launch it.

        The 'now' parameter is ignored.
        """
        self.shutdown_kernel()
        self.start_kernel(**kwds)

    @property
    def has_kernel(self):
        """ Returns whether a kernel process has been specified for the kernel
        manager.
        """
        return self.kernel is not None

    def kill_kernel(self):
        """ Kill the running kernel. 
        """
        self.kernel.frontends.remove(self)
        self.kernel = None

    def interrupt_kernel(self):
        """ Interrupts the kernel. """
        raise NotImplementedError("Cannot interrupt embedded kernel.")

    def signal_kernel(self, signum):
        """ Sends a signal to the kernel. """
        raise NotImplementedError("Cannot signal embedded kernel.")

    @property
    def is_alive(self):
        """ Is the kernel process still running? """
        return True

    #--------------------------------------------------------------------------
    # Channels used for communication with the kernel:
    #--------------------------------------------------------------------------

    @property
    def shell_channel(self):
        """Get the REQ socket channel object to make requests of the kernel."""
        if self._shell_channel is None:
            self._shell_channel = self.shell_channel_class(self)
        return self._shell_channel

    @property
    def sub_channel(self):
        """Get the SUB socket channel object."""
        if self._sub_channel is None:
            self._sub_channel = self.sub_channel_class(self)
        return self._sub_channel

    @property
    def stdin_channel(self):
        """Get the REP socket channel object to handle stdin (raw_input)."""
        if self._stdin_channel is None:
            self._stdin_channel = self.stdin_channel_class(self)
        return self._stdin_channel

    @property
    def hb_channel(self):
        """Get the heartbeat socket channel object to check that the
        kernel is alive."""
        if self._hb_channel is None:
            self._hb_channel = self.hb_channel_class(self)
        return self._hb_channel
