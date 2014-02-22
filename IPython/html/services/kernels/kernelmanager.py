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

import os

from tornado import web

from IPython.kernel.multikernelmanager import MultiKernelManager
from IPython.utils.traitlets import (
    Dict, List, Unicode,
)

from IPython.html.utils import to_os_path
from IPython.utils.py3compat import getcwd

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class MappingKernelManager(MultiKernelManager):
    """A KernelManager that handles notebook mapping and HTTP error handling"""

    def _kernel_manager_class_default(self):
        return "IPython.kernel.ioloop.IOLoopKernelManager"

    kernel_argv = List(Unicode)
    
    root_dir = Unicode(getcwd(), config=True)

    def _root_dir_changed(self, name, old, new):
        """Do a bit of validation of the root dir."""
        if not os.path.isabs(new):
            # If we receive a non-absolute path, make it absolute.
            self.root_dir = os.path.abspath(new)
            return
        if not os.path.exists(new) or not os.path.isdir(new):
            raise TraitError("kernel root dir %r is not a directory" % new)

    #-------------------------------------------------------------------------
    # Methods for managing kernels and sessions
    #-------------------------------------------------------------------------

    def _handle_kernel_died(self, kernel_id):
        """notice that a kernel died"""
        self.log.warn("Kernel %s died, removing from map.", kernel_id)
        self.remove_kernel(kernel_id)
    
    def cwd_for_path(self, path):
        """Turn API path into absolute OS path."""
        os_path = to_os_path(path, self.root_dir)
        # in the case of notebooks and kernels not being on the same filesystem,
        # walk up to root_dir if the paths don't exist
        while not os.path.exists(os_path) and os_path != self.root_dir:
            os_path = os.path.dirname(os_path)
        return os_path

    def start_kernel(self, kernel_id=None, path=None, **kwargs):
        """Start a kernel for a session an return its kernel_id.

        Parameters
        ----------
        kernel_id : uuid
            The uuid to associate the new kernel with. If this
            is not None, this kernel will be persistent whenever it is 
            requested.
        path : API path
            The API path (unicode, '/' delimited) for the cwd.
            Will be transformed to an OS path relative to root_dir.
        """
        if kernel_id is None:
            kwargs['extra_arguments'] = self.kernel_argv
            if path is not None:
                kwargs['cwd'] = self.cwd_for_path(path)
            kernel_id = super(MappingKernelManager, self).start_kernel(**kwargs)
            self.log.info("Kernel started: %s" % kernel_id)
            self.log.debug("Kernel args: %r" % kwargs)
            # register callback for failed auto-restart
            self.add_restart_callback(kernel_id,
                lambda : self._handle_kernel_died(kernel_id),
                'dead',
            )
        else:
            self._check_kernel_id(kernel_id)
            self.log.info("Using existing kernel: %s" % kernel_id)
        return kernel_id

    def shutdown_kernel(self, kernel_id, now=False):
        """Shutdown a kernel by kernel_id"""
        self._check_kernel_id(kernel_id)
        super(MappingKernelManager, self).shutdown_kernel(kernel_id, now=now)

    def kernel_model(self, kernel_id):
        """Return a dictionary of kernel information described in the
        JSON standard model."""
        self._check_kernel_id(kernel_id)
        model = {"id":kernel_id}
        return model

    def list_kernels(self):
        """Returns a list of kernel_id's of kernels running."""
        kernels = []
        kernel_ids = super(MappingKernelManager, self).list_kernel_ids()
        for kernel_id in kernel_ids:
            model = self.kernel_model(kernel_id)
            kernels.append(model)
        return kernels

    # override _check_kernel_id to raise 404 instead of KeyError
    def _check_kernel_id(self, kernel_id):
        """Check a that a kernel_id exists and raise 404 if not."""
        if kernel_id not in self:
            raise web.HTTPError(404, u'Kernel does not exist: %s' % kernel_id)
