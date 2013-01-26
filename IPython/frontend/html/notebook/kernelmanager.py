"""A kernel manager relating notebooks and kernels

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

from tornado import web

from IPython.kernel.multikernelmanager import MultiKernelManager
from IPython.utils.traitlets import (
    Dict, List, Unicode, Float, Integer,
)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class MappingKernelManager(MultiKernelManager):
    """A KernelManager that handles notebok mapping and HTTP error handling"""

    kernel_argv = List(Unicode)
    
    time_to_dead = Float(3.0, config=True, help="""Kernel heartbeat interval in seconds.""")
    first_beat = Float(5.0, config=True, help="Delay (in seconds) before sending first heartbeat.")
    
    max_msg_size = Integer(65536, config=True, help="""
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

    def start_kernel(self, notebook_id=None, **kwargs):
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
            kwargs['extra_arguments'] = self.kernel_argv
            kernel_id = super(MappingKernelManager, self).start_kernel(**kwargs)
            self.set_kernel_for_notebook(notebook_id, kernel_id)
            self.log.info("Kernel started: %s" % kernel_id)
            self.log.debug("Kernel args: %r" % kwargs)
        else:
            self.log.info("Using existing kernel: %s" % kernel_id)
        return kernel_id

    def shutdown_kernel(self, kernel_id, now=False):
        """Shutdown a kernel and remove its notebook association."""
        self._check_kernel_id(kernel_id)
        super(MappingKernelManager, self).shutdown_kernel(
            kernel_id, now=now
        )
        self.delete_mapping_for_kernel(kernel_id)
        self.log.info("Kernel shutdown: %s" % kernel_id)

    def interrupt_kernel(self, kernel_id):
        """Interrupt a kernel."""
        self._check_kernel_id(kernel_id)
        super(MappingKernelManager, self).interrupt_kernel(kernel_id)
        self.log.info("Kernel interrupted: %s" % kernel_id)

    def restart_kernel(self, kernel_id):
        """Restart a kernel while keeping clients connected."""
        self._check_kernel_id(kernel_id)
        super(MappingKernelManager, self).restart_kernel(kernel_id)
        self.log.info("Kernel restarted: %s" % kernel_id)

    def create_iopub_stream(self, kernel_id):
        """Create a new iopub stream."""
        self._check_kernel_id(kernel_id)
        return super(MappingKernelManager, self).create_iopub_stream(kernel_id)

    def create_shell_stream(self, kernel_id):
        """Create a new shell stream."""
        self._check_kernel_id(kernel_id)
        return super(MappingKernelManager, self).create_shell_stream(kernel_id)

    def create_hb_stream(self, kernel_id):
        """Create a new hb stream."""
        self._check_kernel_id(kernel_id)
        return super(MappingKernelManager, self).create_hb_stream(kernel_id)

    def _check_kernel_id(self, kernel_id):
        """Check a that a kernel_id exists and raise 404 if not."""
        if kernel_id not in self:
            raise web.HTTPError(404, u'Kernel does not exist: %s' % kernel_id)

