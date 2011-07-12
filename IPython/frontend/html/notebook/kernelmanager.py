"""A kernel manager for multiple kernels."""

import logging
import signal
import sys
import uuid

import zmq

from IPython.config.configurable import Configurable
from IPython.zmq.ipkernel import launch_kernel
from IPython.utils.traitlets import Instance, Dict, Unicode


class DuplicateKernelError(Exception):
    pass


class KernelManager(Configurable):
    """A class for managing multiple kernels."""

    context = Instance('zmq.Context')
    def _context_default(self):
        return zmq.Context.instance()

    logname = Unicode('')
    def _logname_changed(self, name, old, new):
        self.log = logging.getLogger(new)

    _kernels = Dict()

    @property
    def kernel_ids(self):
        """Return a list of the kernel ids of the active kernels."""
        return self._kernels.keys()

    def __len__(self):
        """Return the number of running kernels."""
        return len(self.kernel_ids)

    def __contains__(self, kernel_id):
        if kernel_id in self.kernel_ids:
            return True
        else:
            return False

    def start_kernel(self, **kwargs):
        """Start a new kernel."""
        kernel_id = str(uuid.uuid4())
        (process, shell_port, iopub_port, stdin_port, hb_port) = launch_kernel(**kwargs)
        # Store the information for contacting the kernel. This assumes the kernel is
        # running on localhost.
        d = dict(
            process = process,
            stdin_port = stdin_port,
            iopub_port = iopub_port,
            shell_port = shell_port,
            hb_port = hb_port,
            ip = '127.0.0.1'
        )
        self._kernels[kernel_id] = d
        return kernel_id

    def kill_kernel(self, kernel_id):
        """Kill a kernel by its kernel uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to kill.
        """
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
        """Interrupt (SIGINT) the kernel by its uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to interrupt.
        """
        kernel_process = self.get_kernel_process(kernel_id)
        if kernel_process is not None:
            if sys.platform == 'win32':
                from parentpoller import ParentPollerWindows as Poller
                Poller.send_interrupt(kernel_process.win32_interrupt_event)
            else:
                kernel_process.send_signal(signal.SIGINT)

    def signal_kernel(self, kernel_id, signum):
        """ Sends a signal to the kernel by its uuid.

        Note that since only SIGTERM is supported on Windows, this function
        is only useful on Unix systems.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to signal.
        """
        kernel_process = self.get_kernel_process(kernel_id)
        if kernel_process is not None:
            kernel_process.send_signal(signum)

    def get_kernel_process(self, kernel_id):
        """Get the process object for a kernel by its uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.
        """
        d = self._kernels.get(kernel_id)
        if d is not None:
            return d['process']
        else:
            raise KeyError("Kernel with id not found: %s" % kernel_id)

    def get_kernel_ports(self, kernel_id):
        """Return a dictionary of ports for a kernel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.

        Returns
        =======
        port_dict : dict
            A dict of key, value pairs where the keys are the names
            (stdin_port,iopub_port,shell_port) and the values are the
            integer port numbers for those channels.
        """
        d = self._kernels.get(kernel_id)
        if d is not None:
            dcopy = d.copy()
            dcopy.pop('process')
            dcopy.pop('ip')
            return dcopy
        else:
            raise KeyError("Kernel with id not found: %s" % kernel_id)

    def get_kernel_ip(self, kernel_id):
        """Return ip address for a kernel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.

        Returns
        =======
        ip : str
            The ip address of the kernel.
        """
        d = self._kernels.get(kernel_id)
        if d is not None:
            return d['ip']
        else:
            raise KeyError("Kernel with id not found: %s" % kernel_id)

    def create_session_manager(self, kernel_id):
        """Create a new session manager for a kernel by its uuid."""
        from sessionmanager import SessionManager
        return SessionManager(
            kernel_id=kernel_id, kernel_manager=self, 
            config=self.config, context=self.context, logname=self.logname
        )

