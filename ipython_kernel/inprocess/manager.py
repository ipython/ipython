"""A kernel manager for in-process kernels."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.utils.traitlets import Instance, DottedObjectName
from jupyter_client.managerabc import KernelManagerABC
from jupyter_client.manager import KernelManager
from jupyter_client.session import Session


class InProcessKernelManager(KernelManager):
    """A manager for an in-process kernel.

    This class implements the interface of
    `jupyter_client.kernelmanagerabc.KernelManagerABC` and allows
    (asynchronous) frontends to be used seamlessly with an in-process kernel.

    See `jupyter_client.kernelmanager.KernelManager` for docstrings.
    """

    # The kernel process with which the KernelManager is communicating.
    kernel = Instance('ipython_kernel.inprocess.ipkernel.InProcessKernel',
                      allow_none=True)
    # the client class for KM.client() shortcut
    client_class = DottedObjectName('ipython_kernel.inprocess.BlockingInProcessKernelClient')

    def _session_default(self):
        # don't sign in-process messages
        return Session(key=b'', parent=self)

    #--------------------------------------------------------------------------
    # Kernel management methods
    #--------------------------------------------------------------------------

    def start_kernel(self, **kwds):
        from ipython_kernel.inprocess.ipkernel import InProcessKernel
        self.kernel = InProcessKernel(parent=self, session=self.session)

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
