"""A basic kernel monitor with autorestarting.

This watches a kernel's state using KernelManager.is_alive and auto
restarts the kernel if it dies.

It is an incomplete base class, and must be subclassed.
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


from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import (
    Instance, Float, List,
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class KernelRestarter(LoggingConfigurable):
    """Monitor and autorestart a kernel."""

    kernel_manager = Instance('IPython.kernel.KernelManager')

    time_to_dead = Float(3.0, config=True,
        help="""Kernel heartbeat interval in seconds."""
    )
    _callbacks = List()

    def start(self):
        """Start the polling of the kernel."""
        raise NotImplementedError("Must be implemented in a subclass")

    def stop(self):
        """Stop the kernel polling."""
        raise NotImplementedError("Must be implemented in a subclass")

    def register_callback(self, f):
        """register a callback to fire"""
        self._callbacks.append(f)

    def unregister_callback(self, f):
        try:
            self._callbacks.remove(f)
        except ValueError:
            pass

    def poll(self):
        self.log.debug('Polling kernel...')
        if not self.kernel_manager.is_alive():
            self.log.info('KernelRestarter: restarting kernel')
            for callback in self._callbacks:
                try:
                    callback()
                except Exception as e:
                    self.log.error("Kernel restart callback %r failed", callback, exc_info=True)
            self.kernel_manager.restart_kernel(now=True)
