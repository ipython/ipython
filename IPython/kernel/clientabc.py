"""Abstract base class for kernel clients"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
import abc

#-----------------------------------------------------------------------------
# Main kernel client class
#-----------------------------------------------------------------------------

class KernelClientABC(object):
    """KernelManager ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.kernel.client.KernelClient`
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
