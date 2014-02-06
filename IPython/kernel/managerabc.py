"""Abstract base class for kernel managers."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import abc

from IPython.utils.py3compat import with_metaclass


class KernelManagerABC(with_metaclass(abc.ABCMeta, object)):
    """KernelManager ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.kernel.kernelmanager.KernelManager`
    """

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

    @abc.abstractmethod
    def is_alive(self):
        pass
