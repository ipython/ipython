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
    Dict, List, Unicode, Integer,
)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class MappingKernelManager(MultiKernelManager):
    """A KernelManager that handles notebook mapping and HTTP error handling"""

    def _kernel_manager_class_default(self):
        return "IPython.kernel.ioloop.IOLoopKernelManager"

    kernel_argv = List(Unicode)
    
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
        for notebook_id, kid in self._notebook_mapping.iteritems():
            if kernel_id == kid:
                return notebook_id
        return None

    def delete_mapping_for_kernel(self, kernel_id):
        """Remove the kernel/notebook mapping for kernel_id."""
        notebook_id = self.notebook_for_kernel(kernel_id)
        if notebook_id is not None:
            del self._notebook_mapping[notebook_id]

    def _handle_kernel_died(self, kernel_id):
        """notice that a kernel died"""
        self.log.warn("Kernel %s died, removing from map.", kernel_id)
        self.delete_mapping_for_kernel(kernel_id)
        self.remove_kernel(kernel_id, now=True)

    def start_kernel(self, notebook_id=None, **kwargs):
        """Start a kernel for a notebook an return its kernel_id.

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
            # register callback for failed auto-restart
            self.add_restart_callback(kernel_id,
                lambda : self._handle_kernel_died(kernel_id),
                'dead',
            )
        else:
            self.log.info("Using existing kernel: %s" % kernel_id)

        return kernel_id

    def shutdown_kernel(self, kernel_id, now=False):
        """Shutdown a kernel by kernel_id"""
        super(MappingKernelManager, self).shutdown_kernel(kernel_id, now=now)
        self.delete_mapping_for_kernel(kernel_id)

    # override _check_kernel_id to raise 404 instead of KeyError
    def _check_kernel_id(self, kernel_id):
        """Check a that a kernel_id exists and raise 404 if not."""
        if kernel_id not in self:
            raise web.HTTPError(404, u'Kernel does not exist: %s' % kernel_id)

