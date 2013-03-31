"""A kernel manager for in-process kernels."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.utils.traitlets import Instance, DottedObjectName
from IPython.kernel.managerabc import KernelManagerABC
from IPython.kernel.manager import KernelManager

#-----------------------------------------------------------------------------
# Main kernel manager class
#-----------------------------------------------------------------------------

class InProcessKernelManager(KernelManager):
    """A manager for an in-process kernel.

    This class implements the interface of
    `IPython.kernel.kernelmanagerabc.KernelManagerABC` and allows
    (asynchronous) frontends to be used seamlessly with an in-process kernel.

    See `IPython.kernel.kernelmanager.KernelManager` for docstrings.
    """

    # The kernel process with which the KernelManager is communicating.
    kernel = Instance('IPython.kernel.inprocess.ipkernel.InProcessKernel')
    # the client class for KM.client() shortcut
    client_class = DottedObjectName('IPython.kernel.inprocess.BlockingInProcessKernelClient')

    #--------------------------------------------------------------------------
    # Kernel management methods
    #--------------------------------------------------------------------------

    def start_kernel(self, **kwds):
        from IPython.kernel.inprocess.ipkernel import InProcessKernel
        self.kernel = InProcessKernel()

    def shutdown_kernel(self):
        self._kill_kernel()

    def restart_kernel(self, now=False, **kwds):
        self.shutdown_kernel()
        self.start_kernel(**kwds)

    @property
    def has_kernel(self):
        return self.kernel is not None

    def _kill_kernel(self):
        self.kernel = None

    def interrupt_kernel(self):
        raise NotImplementedError("Cannot interrupt in-process kernel.")

    def signal_kernel(self, signum):
        raise NotImplementedError("Cannot signal in-process kernel.")

    def is_alive(self):
        return self.kernel is not None

    def client(self, **kwargs):
        kwargs['kernel'] = self.kernel
        return super(InProcessKernelManager, self).client(**kwargs)


#-----------------------------------------------------------------------------
# ABC Registration
#-----------------------------------------------------------------------------

KernelManagerABC.register(InProcessKernelManager)
