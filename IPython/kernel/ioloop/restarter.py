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


from IPython.kernel.restarter import KernelRestarter
from IPython.utils.traitlets import (
    Instance, Float, List,
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class IOLoopKernelRestarter(KernelRestarter):
    """Monitor and autorestart a kernel."""

    loop = Instance('zmq.eventloop.ioloop.IOLoop', allow_none=False)
    def _loop_default(self):
        return ioloop.IOLoop.instance()

    time_to_dead = Float(3.0, config=True,
        help="""Kernel heartbeat interval in seconds."""
    )

    _pcallback = None

    def start(self):
        """Start the polling of the kernel."""
        if self._pcallback is None:
            self._pcallback = ioloop.PeriodicCallback(
                self.poll, 1000*self.time_to_dead, self.loop
            )
        self._pcallback.start()

    def stop(self):
        """Stop the kernel polling."""
        if self._pcallback is not None:
            self._pcallback.stop()

    def clear(self):
        """Clear the underlying PeriodicCallback."""
        self.stop()
        self._pcallback = None
