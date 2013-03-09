"""A kernel manager for multiple kernels

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import absolute_import

import os
import uuid

import zmq
from zmq.eventloop.zmqstream import ZMQStream

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import (
    Instance, Dict, Unicode, Any, DottedObjectName, Bool
)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class DuplicateKernelError(Exception):
    pass


class MultiKernelManager(LoggingConfigurable):
    """A class for managing multiple kernels."""
    
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

    def start_kernel(self, **kwargs):
        """Start a new kernel.

        The caller can pick a kernel_id by passing one in as a keyword arg,
        otherwise one will be picked using a uuid.

        To silence the kernel's stdout/stderr, call this using::

            km.start_kernel(stdout=PIPE, stderr=PIPE)

        """
        kernel_id = kwargs.pop('kernel_id', unicode(uuid.uuid4()))
        if kernel_id in self:
            raise DuplicateKernelError('Kernel already exists: %s' % kernel_id)
        # kernel_manager_factory is the constructor for the KernelManager
        # subclass we are using. It can be configured as any Configurable,
        # including things like its transport and ip.
        km = self.kernel_manager_factory(connection_file=os.path.join(
                    self.connection_dir, "kernel-%s.json" % kernel_id),
                    config=self.config, autorestart=True, log=self.log
        )
        km.start_kernel(**kwargs)
        # start just the shell channel, needed for graceful restart
        km.start_channels(shell=True, iopub=False, stdin=False, hb=False)
        self._kernels[kernel_id] = km
        return kernel_id

    def shutdown_kernel(self, kernel_id, now=False):
        """Shutdown a kernel by its kernel uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to shutdown.
        now : bool
            Should the kernel be shutdown forcibly using a signal.
        """
        k = self.get_kernel(kernel_id)
        k.shutdown_kernel(now=now)
        k.shell_channel.stop()
        del self._kernels[kernel_id]

    def shutdown_all(self, now=False):
        """Shutdown all kernels."""
        for kid in self.list_kernel_ids():
            self.shutdown_kernel(kid, now=now)

    def interrupt_kernel(self, kernel_id):
        """Interrupt (SIGINT) the kernel by its uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to interrupt.
        """
        return self.get_kernel(kernel_id).interrupt_kernel()

    def signal_kernel(self, kernel_id, signum):
        """Sends a signal to the kernel by its uuid.

        Note that since only SIGTERM is supported on Windows, this function
        is only useful on Unix systems.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to signal.
        """
        return self.get_kernel(kernel_id).signal_kernel(signum)

    def restart_kernel(self, kernel_id):
        """Restart a kernel by its uuid, keeping the same ports.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel to interrupt.
        """
        km = self.get_kernel(kernel_id)
        km.restart_kernel()

    def is_alive(self, kernel_id):
        """Is the kernel alive.

        This calls KernelManager.is_alive() which calls Popen.poll on the
        actual kernel subprocess.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.
        """
        return self.get_kernel(kernel_id).is_alive()

    def get_kernel(self, kernel_id):
        """Get the single KernelManager object for a kernel by its uuid.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.
        """
        km = self._kernels.get(kernel_id)
        if km is not None:
            return km
        else:
            raise KeyError("Kernel with id not found: %s" % kernel_id)

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
        km = self.get_kernel(kernel_id)
        return dict(transport=km.transport,
                    ip=km.ip,
                    shell_port=km.shell_port,
                    iopub_port=km.iopub_port,
                    stdin_port=km.stdin_port,
                    hb_port=km.hb_port,
        )  

    def _make_url(self, transport, ip, port):
        """Make a ZeroMQ URL for a given transport, ip and port."""
        if transport == 'tcp':
            return "tcp://%s:%i" % (ip, port)
        else:
            return "%s://%s-%s" % (transport, ip, port)

    def _create_connected_stream(self, kernel_id, socket_type, channel):
        """Create a connected ZMQStream for a kernel."""
        cinfo = self.get_connection_info(kernel_id)
        url = self._make_url(cinfo['transport'], cinfo['ip'],
                cinfo['%s_port' % channel]
        )
        sock = self.context.socket(socket_type)
        self.log.info("Connecting to: %s" % url)
        sock.connect(url)
        return ZMQStream(sock)

    def create_iopub_stream(self, kernel_id):
        """Return a ZMQStream object connected to the iopub channel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.

        Returns
        =======
        stream : ZMQStream
        """
        iopub_stream = self._create_connected_stream(kernel_id, zmq.SUB, 'iopub')
        iopub_stream.socket.setsockopt(zmq.SUBSCRIBE, b'')
        return iopub_stream

    def create_shell_stream(self, kernel_id):
        """Return a ZMQStream object connected to the shell channel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.

        Returns
        =======
        stream : ZMQStream
        """
        shell_stream = self._create_connected_stream(kernel_id, zmq.DEALER, 'shell')
        return shell_stream

    def create_hb_stream(self, kernel_id):
        """Return a ZMQStream object connected to the hb channel.

        Parameters
        ==========
        kernel_id : uuid
            The id of the kernel.

        Returns
        =======
        stream : ZMQStream
        """
        hb_stream = self._create_connected_stream(kernel_id, zmq.REQ, 'hb')
        return hb_stream

