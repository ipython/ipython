"""A basic in process kernel monitor with autorestarting.

This watches a kernel's state using KernelManager.is_alive and auto
restarts the kernel if it dies.
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

import zmq
from zmq.eventloop import ioloop


from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import (
    Instance, Float
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class IOLoopKernelRestarter(LoggingConfigurable):
    """Monitor and autorestart a kernel."""

    loop = Instance('zmq.eventloop.ioloop.IOLoop', allow_none=False)
    def _loop_default(self):
        return ioloop.IOLoop.instance()

    kernel_manager = Instance('IPython.kernel.kernelmanager.KernelManager')

    time_to_dead = Float(3.0, config=True,
        help="""Kernel heartbeat interval in seconds."""
    )

    _pcallback = None

    def start(self):
        """Start the polling of the kernel."""
        if self._pcallback is None:
            self._pcallback = ioloop.PeriodicCallback(
                self._poll, 1000*self.time_to_dead, self.loop
            )
        self._pcallback.start()

    def stop(self):
        """Stop the kernel polling."""
        if self._pcallback is not None:
            self._pcallback.stop()

    def clear(self):
        """Clear the underlying PeriodicCallback."""
        self.stop()
        if self._pcallback is not None:
            self._pcallback = None

    def _poll(self):
        self.log.info('Polling kernel...')
        if not self.kernel_manager.is_alive():
            # This restart event should leave the connection file in place so
            # the ports are the same. Because this takes place below the
            # MappingKernelManager, the kernel_id will also remain the same.
            self.log.info('KernelRestarter: restarting kernel')
            self.kernel_manager.restart_kernel(now=True);
