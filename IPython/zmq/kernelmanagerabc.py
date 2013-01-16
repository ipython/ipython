"""Abstract base classes for kernel manager and channels."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports.
import abc

#-----------------------------------------------------------------------------
# Channels
#-----------------------------------------------------------------------------


class ChannelABC(object):
    """A base class for all channel ABCs."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def is_alive(self):
        pass


class ShellChannelABC(ChannelABC):
    """The DEALER channel for issues request/replies to the kernel.
    """

    @abc.abstractproperty
    def allow_stdin(self):
        pass

    @abc.abstractmethod
    def execute(self, code, silent=False, store_history=True,
                user_variables=None, user_expressions=None, allow_stdin=None):
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
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def history(self, raw=True, output=False, hist_access_type='range', **kwargs):
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
        pass

    @abc.abstractmethod
    def kernel_info(self):
        """Request kernel info."""
        pass

    @abc.abstractmethod
    def shutdown(self, restart=False):
        """Request an immediate kernel shutdown.

        Upon receipt of the (empty) reply, client code can safely assume that
        the kernel has shut down and it's safe to forcefully terminate it if
        it's still alive.

        The kernel will send the reply via a function registered with Python's
        atexit module, ensuring it's truly done as the kernel is done with all
        normal operation.
        """
        pass


class IOPubChannelABC(ChannelABC):
    """The SUB channel which listens for messages that the kernel publishes."""


    @abc.abstractmethod
    def flush(self, timeout=1.0):
        """Immediately processes all pending messages on the SUB channel.

        Callers should use this method to ensure that :method:`call_handlers`
        has been called for all messages that have been received on the
        0MQ SUB socket of this channel.

        This method is thread safe.

        Parameters
        ----------
        timeout : float, optional
            The maximum amount of time to spend flushing, in seconds. The
            default is one second.
        """
        pass


class StdInChannelABC(ChannelABC):
    """A reply channel to handle raw_input requests that the kernel makes."""

    @abc.abstractmethod
    def input(self, string):
        """Send a string of raw input to the kernel."""
        pass


class HBChannelABC(ChannelABC):
    """The heartbeat channel which monitors the kernel heartbeat."""

    @abc.abstractproperty
    def time_to_dead(self):
        pass

    @abc.abstractmethod
    def pause(self):
        """Pause the heartbeat."""
        pass

    @abc.abstractmethod
    def unpause(self):
        """Unpause the heartbeat."""
        pass

    @abc.abstractmethod
    def is_beating(self):
        """Is the heartbeat running and responsive (and not paused)."""
        pass


#-----------------------------------------------------------------------------
# Main kernel manager class
#-----------------------------------------------------------------------------

class KernelManagerABC(object):
    """ Manages a kernel for a frontend."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def kernel(self):
        pass

    @abc.abstractproperty
    def shell_channel_class(self):
        pass

    @abc.abstractproperty
    def iopub_channel_class(self):
        pass

    @abc.abstractproperty
    def hb_channel_class(self):
        pass

    @abc.abstractproperty
    def stdin_channel_class(self):
        pass

    #--------------------------------------------------------------------------
    # Channel management methods:
    #--------------------------------------------------------------------------

    @abc.abstractmethod
    def start_channels(self, shell=True, iopub=True, stdin=True, hb=True):
        """Starts the channels for this kernel.

        This will create the channels if they do not exist and then start
        them. If port numbers of 0 are being used (random ports) then you
        must first call :method:`start_kernel`. If the channels have been
        stopped and you call this, :class:`RuntimeError` will be raised.
        """
        pass

    @abc.abstractmethod
    def stop_channels(self):
        """Stops all the running channels for this kernel."""
        pass

    @abc.abstractproperty
    def channels_running(self):
        """Are any of the channels created and running?"""
        pass

    @abc.abstractproperty
    def shell_channel(self):
        """Get the REQ socket channel object to make requests of the kernel."""
        pass

    @abc.abstractproperty
    def iopub_channel(self):
        """Get the SUB socket channel object."""
        pass

    @abc.abstractproperty
    def stdin_channel(self):
        """Get the REP socket channel object to handle stdin (raw_input)."""
        pass

    @abc.abstractproperty
    def hb_channel(self):
        """Get the heartbeat socket channel object to check that the
        kernel is alive."""
        pass

    #--------------------------------------------------------------------------
    # Kernel management.
    #--------------------------------------------------------------------------

    @abc.abstractmethod
    def start_kernel(self, **kw):
        """Starts a kernel process and configures the manager to use it.

        If random ports (port=0) are being used, this method must be called
        before the channels are created.

        Parameters:
        -----------
        launcher : callable, optional (default None)
             A custom function for launching the kernel process (generally a
             wrapper around ``entry_point.base_launch_kernel``). In most cases,
             it should not be necessary to use this parameter.

        **kw : optional
             See respective options for IPython and Python kernels.
        """
        pass

    @abc.abstractmethod
    def shutdown_kernel(self, now=False, restart=False):
        """ Attempts to the stop the kernel process cleanly."""
        pass

    @abc.abstractmethod
    def restart_kernel(self, now=False, **kw):
        """Restarts a kernel with the arguments that were used to launch it.

        If the old kernel was launched with random ports, the same ports will be
        used for the new kernel.

        Parameters
        ----------
        now : bool, optional
            If True, the kernel is forcefully restarted *immediately*, without
            having a chance to do any cleanup action.  Otherwise the kernel is
            given 1s to clean up before a forceful restart is issued.

            In all cases the kernel is restarted, the only difference is whether
            it is given a chance to perform a clean shutdown or not.

        **kw : optional
            Any options specified here will replace those used to launch the
            kernel.
        """
        pass

    @abc.abstractproperty
    def has_kernel(self):
        """Returns whether a kernel process has been specified for the kernel
        manager.
        """
        pass

    @abc.abstractmethod
    def kill_kernel(self):
        """ Kill the running kernel.

        This method blocks until the kernel process has terminated.
        """
        pass

    @abc.abstractmethod
    def interrupt_kernel(self):
        """ Interrupts the kernel.

        Unlike ``signal_kernel``, this operation is well supported on all
        platforms.
        """
        pass

    @abc.abstractmethod
    def signal_kernel(self, signum):
        """ Sends a signal to the kernel.

        Note that since only SIGTERM is supported on Windows, this function is
        only useful on Unix systems.
        """
        pass

    @abc.abstractproperty
    def is_alive(self):
        """Is the kernel process still running?"""
        pass
