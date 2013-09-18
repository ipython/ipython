"""A client for in-process kernels."""

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
from IPython.utils.traitlets import Type, Instance
from IPython.kernel.clientabc import KernelClientABC
from IPython.kernel.client import KernelClient

# Local imports
from .channels import (
    InProcessShellChannel,
    InProcessIOPubChannel,
    InProcessHBChannel,
    InProcessStdInChannel,

)

#-----------------------------------------------------------------------------
# Main kernel Client class
#-----------------------------------------------------------------------------

class InProcessKernelClient(KernelClient):
    """A client for an in-process kernel.

    This class implements the interface of
    `IPython.kernel.clientabc.KernelClientABC` and allows
    (asynchronous) frontends to be used seamlessly with an in-process kernel.

    See `IPython.kernel.client.KernelClient` for docstrings.
    """

    # The classes to use for the various channels.
    shell_channel_class = Type(InProcessShellChannel)
    iopub_channel_class = Type(InProcessIOPubChannel)
    stdin_channel_class = Type(InProcessStdInChannel)
    hb_channel_class = Type(InProcessHBChannel)

    kernel = Instance('IPython.kernel.inprocess.ipkernel.Kernel')

    #--------------------------------------------------------------------------
    # Channel management methods
    #--------------------------------------------------------------------------

    def start_channels(self, *args, **kwargs):
        super(InProcessKernelClient, self).start_channels(self)
        self.kernel.frontends.append(self)

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


#-----------------------------------------------------------------------------
# ABC Registration
#-----------------------------------------------------------------------------

KernelClientABC.register(InProcessKernelClient)
