"""A kernel manager for multiple kernels"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import

import os
import uuid

import zmq

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import (
    Instance, Dict, List, Unicode, Any, DottedObjectName
)
from IPython.utils.py3compat import unicode_type

from .kernelspec import NATIVE_KERNEL_NAME

class DuplicateKernelError(Exception):
    pass


def kernel_method(f):
    """decorator for proxying MKM.method(kernel_id) to individual KMs by ID"""
    def wrapped(self, kernel_id, *args, **kwargs):
        # get the kernel
        km = self.get_kernel(kernel_id)
        method = getattr(km, f.__name__)
        # call the kernel's method
        r = method(*args, **kwargs)
        # last thing, call anything defined in the actual class method
        # such as logging messages
        f(self, kernel_id, *args, **kwargs)
        # return the method result
        return r
    return wrapped


class MultiKernelManager(LoggingConfigurable):
    """A class for managing multiple kernels."""
    
    ipython_kernel_argv = List(Unicode)

    default_kernel_name = Unicode(NATIVE_KERNEL_NAME, config=True,
        help="The name of the default kernel to start"
    )
    
    kernel_manager_class = DottedObjectName(
        "IPython.kernel.ioloop.IOLoopKernelManager", config=True,
        help="""The kernel manager class.  This is configurable to allow
        subclassing of the KernelManager for customized behavior.
        """
    )
    def _kernel_manager_class_changed(self, name, old, new):
        self.kernel_manager_factory = import_item(new)
    
    kernel_manager_factory = Any(help="this is kernel_manager_class after import")
    def _kernel_manager_factory_default(self):
        return import_item(self.kernel_manager_class)
    
    context = Instance('zmq.Context')
    def _context_default(self):
        return zmq.Context.instance()

    connection_dir = Unicode('')

    _kernels = Dict()

    def list_kernel_ids(self):
        """Return a list of the kernel ids of the active kernels."""
        # Create a copy so we can iterate over kernels in operations
        # that delete keys.
        return list(self._kernels.keys())

    def __len__(self):
        """Return the number of running kernels."""
        return len(self.list_kernel_ids())

    def __contains__(self, kernel_id):
        return kernel_id in self._kernels

    def start_kernel(self, kernel_name=None, **kwargs):
        """Start a new kernel.

        The caller can pick a kernel_id by passing one in as a keyword arg,
        otherwise one will be picked using a uuid.

        To silence the kernel's stdout/stderr, call this using::

            km.start_kernel(stdout=PIPE, stderr=PIPE)

        """
        kernel_id = kwargs.pop('kernel_id', unicode_type(uuid.uuid4()))
        if kernel_id in self:
            raise DuplicateKernelError('Kernel already exists: %s' % kernel_id)
        
        if kernel_name is None:
            kernel_name = self.default_kernel_name
        # kernel_manager_factory is the constructor for the KernelManager
        # subclass we are using. It can be configured as any Configurable,
        # including things like its transport and ip.
        km = self.kernel_manager_factory(connection_file=os.path.join(
                    self.connection_dir, "kernel-%s.json" % kernel_id),
                    parent=self, autorestart=True, log=self.log, kernel_name=kernel_name,
        )
        # FIXME: remove special treatment of IPython kernels
        if km.ipython_kernel:
            kwargs.setdefault('extra_arguments', self.ipython_kernel_argv)
        km.start_kernel(**kwargs)
        self._kernels[kernel_id] = km
        return kernel_id

    @kernel_method
    def shutdown_kernel(self, kernel_id, now=False, restart=False):
        """Shutdown a kernel by its kernel uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to shutdown.
        now : bool
            Should the kernel be shutdown forcibly using a signal.
        restart : bool
            Will the kernel be restarted?
        """
        self.log.info("Kernel shutdown: %s" % kernel_id)
        self.remove_kernel(kernel_id)

    @kernel_method
    def request_shutdown(self, kernel_id, restart=False):
        """Ask a kernel to shut down by its kernel uuid"""

    @kernel_method
    def finish_shutdown(self, kernel_id, waittime=1, pollinterval=0.1):
        """Wait for a kernel to finish shutting down, and kill it if it doesn't
        """
        self.log.info("Kernel shutdown: %s" % kernel_id)

    @kernel_method
    def cleanup(self, kernel_id, connection_file=True):
        """Clean up a kernel's resources"""

    def remove_kernel(self, kernel_id):
        """remove a kernel from our mapping.

        Mainly so that a kernel can be removed if it is already dead,
        without having to call shutdown_kernel.

        The kernel object is returned.
        """
        return self._kernels.pop(kernel_id)

    def shutdown_all(self, now=False):
        """Shutdown all kernels."""
        kids = self.list_kernel_ids()
        for kid in kids:
            self.request_shutdown(kid)
        for kid in kids:
            self.finish_shutdown(kid)
            self.cleanup(kid)
            self.remove_kernel(kid)

    @kernel_method
    def interrupt_kernel(self, kernel_id):
        """Interrupt (SIGINT) the kernel by its uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to interrupt.
        """
        self.log.info("Kernel interrupted: %s" % kernel_id)

    @kernel_method
    def signal_kernel(self, kernel_id, signum):
        """Sends a signal to the kernel by its uuid.

        Note that since only SIGTERM is supported on Windows, this function
        is only useful on Unix systems.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to signal.
        """
        self.log.info("Signaled Kernel %s with %s" % (kernel_id, signum))

    @kernel_method
    def restart_kernel(self, kernel_id, now=False):
        """Restart a kernel by its uuid, keeping the same ports.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to interrupt.
        """
        self.log.info("Kernel restarted: %s" % kernel_id)

    @kernel_method
    def is_alive(self, kernel_id):
        """Is the kernel alive.

        This calls KernelManager.is_alive() which calls Popen.poll on the
        actual kernel subprocess.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.
        """

    def _check_kernel_id(self, kernel_id):
        """check that a kernel id is valid"""
        if kernel_id not in self:
            raise KeyError("Kernel with id not found: %s" % kernel_id)

    def get_kernel(self, kernel_id):
        """Get the single KernelManager object for a kernel by its uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.
        """
        self._check_kernel_id(kernel_id)
        return self._kernels[kernel_id]

    @kernel_method
    def add_restart_callback(self, kernel_id, callback, event='restart'):
        """add a callback for the KernelRestarter"""

    @kernel_method
    def remove_restart_callback(self, kernel_id, callback, event='restart'):
        """remove a callback for the KernelRestarter"""

    @kernel_method
    def get_connection_info(self, kernel_id):
        """Return a dictionary of connection data for a kernel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.

        Returns
        =======
        connection_dict : dict
            A dict of the information needed to connect to a kernel.
            This includes the ip address and the integer port
            numbers of the different channels (stdin_port, iopub_port,
            shell_port, hb_port).
        """

    @kernel_method
    def connect_iopub(self, kernel_id, identity=None):
        """Return a zmq Socket connected to the iopub channel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel
        identity : bytes (optional)
            The zmq identity of the socket

        Returns
        =======
        stream : zmq Socket or ZMQStream
        """

    @kernel_method
    def connect_shell(self, kernel_id, identity=None):
        """Return a zmq Socket connected to the shell channel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel
        identity : bytes (optional)
            The zmq identity of the socket

        Returns
        =======
        stream : zmq Socket or ZMQStream
        """

    @kernel_method
    def connect_stdin(self, kernel_id, identity=None):
        """Return a zmq Socket connected to the stdin channel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel
        identity : bytes (optional)
            The zmq identity of the socket

        Returns
        =======
        stream : zmq Socket or ZMQStream
        """

    @kernel_method
    def connect_hb(self, kernel_id, identity=None):
        """Return a zmq Socket connected to the hb channel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel
        identity : bytes (optional)
            The zmq identity of the socket

        Returns
        =======
        stream : zmq Socket or ZMQStream
        """
