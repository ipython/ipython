import signal
import sys

from IPython.zmq.ipkernel import launch_kernel
from session import SessionManager


class DuplicateKernelError(Exception):
    pass


class KernelManager(object):

    ip = '127.0.0.1'

    def __init__(self, context):
        self.context = context
        self._kernels = {}

    @property
    def kernel_ids(self):
        return self._kernels.keys()

    def __len__(self):
        return len(self.kernel_ids)

    def __contains__(self, kernel_id):
        if kernel_id in self.kernel_ids:
            return True
        else:
            return False

    def start_kernel(self, kernel_id):
        if kernel_id in self._kernels:
            raise DuplicateKernelError("Kernel already exists: %s" % kernel_id)
        (process, shell_port, iopub_port, stdin_port, hb_port) = launch_kernel()
        d = dict(
            process = process,
            stdin_port = stdin_port,
            iopub_port = iopub_port,
            shell_port = shell_port,
            hb_port = hb_port,
            session_manager = SessionManager(self, kernel_id, self.context)
        )
        self._kernels[kernel_id] = d
        return kernel_id

    def kill_kernel(self, kernel_id):
        kernel_process = self.get_kernel_process(kernel_id)
        if kernel_process is not None:
            # Attempt to kill the kernel.
            try:
                kernel_process.kill()
            except OSError, e:
                # In Windows, we will get an Access Denied error if the process
                # has already terminated. Ignore it.
                if not (sys.platform == 'win32' and e.winerror == 5):
                    raise
            del self._kernels[kernel_id]

    def interrupt_kernel(self, kernel_id):
        kernel_process = self.get_kernel_process(kernel_id)
        if kernel_process is not None:
            if sys.platform == 'win32':
                from parentpoller import ParentPollerWindows as Poller
                Poller.send_interrupt(kernel_process.win32_interrupt_event)
            else:
                kernel_process.send_signal(signal.SIGINT)

    def signal_kernel(self, kernel_id, signum):
        """ Sends a signal to the kernel. Note that since only SIGTERM is
        supported on Windows, this function is only useful on Unix systems.
        """
        kernel_process = self.get_kernel_process(kernel_id)
        if kernel_process is not None:
            kernel_process.send_signal(signum)

    def get_kernel_process(self, kernel_id):
        d = self._kernels.get(kernel_id)
        if d is not None:
            return d['process']
        else:
            raise KeyError("Kernel with id not found: %s" % kernel_id)

    def get_kernel_ports(self, kernel_id):
        d = self._kernels.get(kernel_id)
        if d is not None:
            dcopy = d.copy()
            dcopy.pop('process')
            return dcopy
        else:
            raise KeyError("Kernel with id not found: %s" % kernel_id)

    def get_session_manager(self, kernel_id):
        d = self._kernels.get(kernel_id)
        if d is not None:
            return d['session_manager']
        else:
            raise KeyError("Kernel with id not found: %s" % kernel_id)



