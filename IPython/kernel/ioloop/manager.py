"""A kernel manager with a tornado IOLoop"""

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

from IPython.utils.traitlets import (
    Instance
)

from IPython.kernel.manager import KernelManager
from .restarter import IOLoopKernelRestarter

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class IOLoopKernelManager(KernelManager):

    loop = Instance('zmq.eventloop.ioloop.IOLoop', allow_none=False)
    def _loop_default(self):
        return ioloop.IOLoop.instance()

    _restarter = Instance('IPython.kernel.ioloop.IOLoopKernelRestarter')

    def start_restarter(self):
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = IOLoopKernelRestarter(
                    kernel_manager=self, loop=self.loop,
                    config=self.config, log=self.log
                )
            self._restarter.start()

    def stop_restarter(self):
        if self.autorestart:
            if self._restarter is not None:
                self._restarter.stop()
