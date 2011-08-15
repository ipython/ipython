"""A kernel manager for multiple kernels."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import signal
import sys
import uuid

import zmq
from zmq.eventloop.zmqstream import ZMQStream

from tornado import web

from IPython.config.configurable import LoggingConfigurable
from IPython.zmq.ipkernel import launch_kernel
from IPython.utils.traitlets import Instance, Dict, List, Unicode, Float, Int

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class DuplicateKernelError(Exception):
    pass


class KernelManager(LoggingConfigurable):
    """A class for managing multiple kernels."""

    context = Instance('zmq.Context')
    def _context_default(self):
        return zmq.Context.instance()

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
        kernel_id = unicode(uuid.uuid4())
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

    def create_connected_stream(self, ip, port, socket_type):
        sock = self.context.socket(socket_type)
        addr = "tcp://%s:%i" % (ip, port)
        self.log.info("Connecting to: %s" % addr)
        sock.connect(addr)
        return ZMQStream(sock)

    def create_iopub_stream(self, kernel_id):
        ip = self.get_kernel_ip(kernel_id)
        ports = self.get_kernel_ports(kernel_id)
        iopub_stream = self.create_connected_stream(ip, ports['iopub_port'], zmq.SUB)
        iopub_stream.socket.setsockopt(zmq.SUBSCRIBE, b'')
        return iopub_stream

    def create_shell_stream(self, kernel_id):
        ip = self.get_kernel_ip(kernel_id)
        ports = self.get_kernel_ports(kernel_id)
        shell_stream = self.create_connected_stream(ip, ports['shell_port'], zmq.XREQ)
        return shell_stream

    def create_hb_stream(self, kernel_id):
        ip = self.get_kernel_ip(kernel_id)
        ports = self.get_kernel_ports(kernel_id)
        hb_stream = self.create_connected_stream(ip, ports['hb_port'], zmq.REQ)
        return hb_stream


class MappingKernelManager(KernelManager):
    """A KernelManager that handles notebok mapping and HTTP error handling"""

    kernel_argv = List(Unicode)
    kernel_manager = Instance(KernelManager)
    time_to_dead = Float(3.0, config=True, help="""Kernel heartbeat interval in seconds.""")
    max_msg_size = Int(65536, config=True, help="""
        The max raw message size accepted from the browser
        over a WebSocket connection.
    """)

    _notebook_mapping = Dict()

    #-------------------------------------------------------------------------
    # Methods for managing kernels and sessions
    #-------------------------------------------------------------------------

    def kernel_for_notebook(self, notebook_id):
        """Return the kernel_id for a notebook_id or None."""
        return self._notebook_mapping.get(notebook_id)

    def set_kernel_for_notebook(self, notebook_id, kernel_id):
        """Associate a notebook with a kernel."""
        if notebook_id is not None:
            self._notebook_mapping[notebook_id] = kernel_id

    def notebook_for_kernel(self, kernel_id):
        """Return the notebook_id for a kernel_id or None."""
        notebook_ids = [k for k, v in self._notebook_mapping.iteritems() if v == kernel_id]
        if len(notebook_ids) == 1:
            return notebook_ids[0]
        else:
            return None

    def delete_mapping_for_kernel(self, kernel_id):
        """Remove the kernel/notebook mapping for kernel_id."""
        notebook_id = self.notebook_for_kernel(kernel_id)
        if notebook_id is not None:
            del self._notebook_mapping[notebook_id]

    def start_kernel(self, notebook_id=None):
        """Start a kernel for a notebok an return its kernel_id.

        Parameters
        ----------
        notebook_id : uuid
            The uuid of the notebook to associate the new kernel with. If this
            is not None, this kernel will be persistent whenever the notebook
            requests a kernel.
        """
        kernel_id = self.kernel_for_notebook(notebook_id)
        if kernel_id is None:
            kwargs = dict()
            kwargs['extra_arguments'] = self.kernel_argv
            kernel_id = super(MappingKernelManager, self).start_kernel(**kwargs)
            self.set_kernel_for_notebook(notebook_id, kernel_id)
            self.log.info("Kernel started: %s" % kernel_id)
            self.log.debug("Kernel args: %r" % kwargs)
        else:
            self.log.info("Using existing kernel: %s" % kernel_id)
        return kernel_id

    def kill_kernel(self, kernel_id):
        """Kill a kernel and remove its notebook association."""
        if kernel_id not in self:
            raise web.HTTPError(404)
        super(MappingKernelManager, self).kill_kernel(kernel_id)
        self.delete_mapping_for_kernel(kernel_id)
        self.log.info("Kernel killed: %s" % kernel_id)

    def interrupt_kernel(self, kernel_id):
        """Interrupt a kernel."""
        if kernel_id not in self:
            raise web.HTTPError(404)
        super(MappingKernelManager, self).interrupt_kernel(kernel_id)
        self.log.info("Kernel interrupted: %s" % kernel_id)

    def restart_kernel(self, kernel_id):
        """Restart a kernel while keeping clients connected."""
        if kernel_id not in self:
            raise web.HTTPError(404)

        # Get the notebook_id to preserve the kernel/notebook association.
        notebook_id = self.notebook_for_kernel(kernel_id)
        # Create the new kernel first so we can move the clients over.
        new_kernel_id = self.start_kernel()
        # Now kill the old kernel.
        self.kill_kernel(kernel_id)
        # Now save the new kernel/notebook association. We have to save it
        # after the old kernel is killed as that will delete the mapping.
        self.set_kernel_for_notebook(notebook_id, new_kernel_id)
        self.log.debug("Kernel restarted: %s" % new_kernel_id)
        return new_kernel_id


