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

from tornado import web

from .routers import IOPubStreamRouter, ShellStreamRouter

from IPython.config.configurable import LoggingConfigurable
from IPython.zmq.ipkernel import launch_kernel
from IPython.utils.traitlets import Instance, Dict, List, Unicode

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

    def create_session_manager(self, kernel_id):
        """Create a new session manager for a kernel by its uuid."""
        from sessionmanager import SessionManager
        return SessionManager(
            kernel_id=kernel_id, kernel_manager=self, 
            config=self.config, context=self.context, log=self.log
        )


class RoutingKernelManager(LoggingConfigurable):
    """A KernelManager that handles WebSocket routing and HTTP error handling"""

    kernel_argv = List(Unicode)
    kernel_manager = Instance(KernelManager)

    _routers = Dict()
    _session_dict = Dict()
    _notebook_mapping = Dict()

    #-------------------------------------------------------------------------
    # Methods for managing kernels and sessions
    #-------------------------------------------------------------------------

    @property
    def kernel_ids(self):
        return self.kernel_manager.kernel_ids

    def notebook_for_kernel(self, kernel_id):
        notebook_ids = [k for k, v in self._notebook_mapping.iteritems() if v == kernel_id]
        if len(notebook_ids) == 1:
            return notebook_ids[0]
        else:
            return None

    def delete_mapping_for_kernel(self, kernel_id):
        notebook_id = self.notebook_for_kernel(kernel_id)
        if notebook_id is not None:
            del self._notebook_mapping[notebook_id]

    def start_kernel(self, notebook_id=None):
        self.log.info
        kernel_id = self._notebook_mapping.get(notebook_id)
        if kernel_id is None:
            kwargs = dict()
            kwargs['extra_arguments'] = self.kernel_argv
            kernel_id = self.kernel_manager.start_kernel(**kwargs)
            if notebook_id is not None:
                self._notebook_mapping[notebook_id] = kernel_id
            self.log.info("Kernel started for notebook %s: %s" % (notebook_id,kernel_id))
            self.log.debug("Kernel args: %r" % kwargs)
            self.start_session_manager(kernel_id)
        else:
            self.log.info("Using existing kernel: %s" % kernel_id)
        return kernel_id

    def start_session_manager(self, kernel_id):
        sm = self.kernel_manager.create_session_manager(kernel_id)
        self._session_dict[kernel_id] = sm
        iopub_stream = sm.get_iopub_stream()
        shell_stream = sm.get_shell_stream()
        iopub_router = IOPubStreamRouter(
            zmq_stream=iopub_stream, session=sm.session, config=self.config
        )
        shell_router = ShellStreamRouter(
            zmq_stream=shell_stream, session=sm.session, config=self.config
        )
        self._routers[(kernel_id, 'iopub')] = iopub_router
        self._routers[(kernel_id, 'shell')] = shell_router

    def kill_kernel(self, kernel_id):
        if kernel_id not in self.kernel_manager:
            raise web.HTTPError(404)
        try:
            sm = self._session_dict.pop(kernel_id)
        except KeyError:
            raise web.HTTPError(404)
        sm.stop()
        self.kernel_manager.kill_kernel(kernel_id)
        self.delete_mapping_for_kernel(kernel_id)
        self.log.info("Kernel killed: %s" % kernel_id)

    def interrupt_kernel(self, kernel_id):
        if kernel_id not in self.kernel_manager:
            raise web.HTTPError(404)
        self.kernel_manager.interrupt_kernel(kernel_id)
        self.log.debug("Kernel interrupted: %s" % kernel_id)

    def restart_kernel(self, kernel_id):
        if kernel_id not in self.kernel_manager:
            raise web.HTTPError(404)

        # Get the notebook_id to preserve the kernel/notebook association
        notebook_id = self.notebook_for_kernel(kernel_id)
        # Create the new kernel first so we can move the clients over.
        new_kernel_id = self.start_kernel()

        # Copy the clients over to the new routers.
        old_iopub_router = self.get_router(kernel_id, 'iopub')
        old_shell_router = self.get_router(kernel_id, 'shell')
        new_iopub_router = self.get_router(new_kernel_id, 'iopub')
        new_shell_router = self.get_router(new_kernel_id, 'shell')
        new_iopub_router.copy_clients(old_iopub_router)
        new_shell_router.copy_clients(old_shell_router)

        # Now shutdown the old session and the kernel.
        # TODO: This causes a hard crash in ZMQStream.close, which sets
        # self.socket to None to hastily. We will need to fix this in PyZMQ
        # itself. For now, we just leave the old kernel running :(
        # Maybe this is fixed now, but nothing was changed really.
        self.kill_kernel(kernel_id)

        # Now save the new kernel/notebook association. We have to save it
        # after the old kernel is killed as that will delete the mapping.
        self._notebook_mapping[notebook_id] = kernel_id

        self.log.debug("Kernel restarted: %s -> %s" % (kernel_id, new_kernel_id))
        return new_kernel_id

    def get_router(self, kernel_id, stream_name):
        router = self._routers[(kernel_id, stream_name)]
        return router

