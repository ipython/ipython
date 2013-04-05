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
    Instance, Float, Dict, Bool,
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

    _restarting = Bool(False)

    callbacks = Dict()
    def _callbacks_default(self):
        return dict(restart=[], dead=[])

    def start(self):
        """Start the polling of the kernel."""
        raise NotImplementedError("Must be implemented in a subclass")

    def stop(self):
        """Stop the kernel polling."""
        raise NotImplementedError("Must be implemented in a subclass")

    def add_callback(self, f, event='restart'):
        """register a callback to fire on a particular event

        Possible values for event:

          'restart' (default): kernel has died, and will be restarted.
          'dead': restart has failed, kernel will be left dead.

        """
        self.callbacks[event].append(f)

    def remove_callback(self, f, event='restart'):
        """unregister a callback to fire on a particular event

        Possible values for event:

          'restart' (default): kernel has died, and will be restarted.
          'dead': restart has failed, kernel will be left dead.

        """
        try:
            self.callbacks[event].remove(f)
        except ValueError:
            pass

    def _fire_callbacks(self, event):
        """fire our callbacks for a particular event"""
        for callback in self.callbacks[event]:
            try:
                callback()
            except Exception as e:
                self.log.error("KernelRestarter: %s callback %r failed", event, callback, exc_info=True)

    def poll(self):
        self.log.debug('Polling kernel...')
        if not self.kernel_manager.is_alive():
            if self._restarting:
                self.log.warn("KernelRestarter: restart failed")
                self._fire_callbacks('dead')
                self._restarting = False
                self.stop()
            else:
                self.log.info('KernelRestarter: restarting kernel')
                self._fire_callbacks('restart')
                self.kernel_manager.restart_kernel(now=True)
                self._restarting = True
        else:
            if self._restarting:
                self.log.debug("KernelRestarter: restart apparently succeeded")
            self._restarting = False
