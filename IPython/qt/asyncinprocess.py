from .inprocess import QtInProcessKernelManager

class QtAsyncInProcessKernelManager(QtInProcessKernelManager):
    def start_kernel(self, **kwds):
        from IPython.kernel.inprocess.asyncipkernel import AsyncInProcessKernel
        self.kernel = AsyncInProcessKernel()
