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

import zmq
from zmq.eventloop import ioloop


from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import (
    Instance, Float
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class KernelRestarter(LoggingConfigurable):
    """Monitor and autorestart a kernel."""

    loop = Instance('zmq.eventloop.ioloop.IOLoop', allow_none=False)
    def _loop_default(self):
        return ioloop.IOLoop.instance()

    kernel_manager = Instance('IPython.kernel.kernelmanager.KernelManager')

    time_to_dead = Float(3.0, config=True,
        help="""Kernel heartbeat interval in seconds."""
    )

    def __init__(self, **kwargs):
        super(KernelRestarter, self).__init__(**kwargs)

    def start(self):
        self.pc = ioloop.PeriodicCallback(self.poll, self.time_to_dead, self.ioloop)
        self.pc.start()

    def poll(self):
        if not self.kernel_manager.is_alive():
            self.stop()
            # This restart event should leave the connection file in place so
            # the ports are the same. Because this takes place below the
            # MappingKernelManager, the kernel_id will also remain the same.
            self.kernel_manager.restart_kernel(now=True);
            self.start()

    def stop(self):
        self.pc.stop()
        self.pc = None
