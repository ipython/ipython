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
    """ShellChannel ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.zmq.kernelmanager.ShellChannel`
    """

    @abc.abstractproperty
    def allow_stdin(self):
        pass

    @abc.abstractmethod
    def execute(self, code, silent=False, store_history=True,
                user_variables=None, user_expressions=None, allow_stdin=None):
        pass

    @abc.abstractmethod
    def complete(self, text, line, cursor_pos, block=None):
        pass

    @abc.abstractmethod
    def object_info(self, oname, detail_level=0):
        pass

    @abc.abstractmethod
    def history(self, raw=True, output=False, hist_access_type='range', **kwargs):
        pass

    @abc.abstractmethod
    def kernel_info(self):
        pass

    @abc.abstractmethod
    def shutdown(self, restart=False):
        pass


class IOPubChannelABC(ChannelABC):
    """IOPubChannel ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.zmq.kernelmanager.IOPubChannel`
    """

    @abc.abstractmethod
    def flush(self, timeout=1.0):
        pass


class StdInChannelABC(ChannelABC):
    """StdInChannel ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.zmq.kernelmanager.StdInChannel`
    """

    @abc.abstractmethod
    def input(self, string):
        pass


class HBChannelABC(ChannelABC):
    """HBChannel ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.zmq.kernelmanager.HBChannel`
    """

    @abc.abstractproperty
    def time_to_dead(self):
        pass

    @abc.abstractmethod
    def pause(self):
        pass

    @abc.abstractmethod
    def unpause(self):
        pass

    @abc.abstractmethod
    def is_beating(self):
        pass


#-----------------------------------------------------------------------------
# Main kernel manager class
#-----------------------------------------------------------------------------

class KernelManagerABC(object):
    """KernelManager ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.zmq.kernelmanager.KernelManager`
    """

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
    # Channel management methods
    #--------------------------------------------------------------------------

    @abc.abstractmethod
    def start_channels(self, shell=True, iopub=True, stdin=True, hb=True):
        pass

    @abc.abstractmethod
    def stop_channels(self):
        pass

    @abc.abstractproperty
    def channels_running(self):
        pass

    @abc.abstractproperty
    def shell_channel(self):
        pass

    @abc.abstractproperty
    def iopub_channel(self):
        pass

    @abc.abstractproperty
    def stdin_channel(self):
        pass

    @abc.abstractproperty
    def hb_channel(self):
        pass

    #--------------------------------------------------------------------------
    # Kernel management
    #--------------------------------------------------------------------------

    @abc.abstractmethod
    def start_kernel(self, **kw):
        pass

    @abc.abstractmethod
    def shutdown_kernel(self, now=False, restart=False):
        pass

    @abc.abstractmethod
    def restart_kernel(self, now=False, **kw):
        pass

    @abc.abstractproperty
    def has_kernel(self):
        pass

    @abc.abstractmethod
    def interrupt_kernel(self):
        pass

    @abc.abstractmethod
    def signal_kernel(self, signum):
        pass

    @abc.abstractproperty
    def is_alive(self):
        pass

