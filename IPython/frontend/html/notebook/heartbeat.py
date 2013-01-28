"""A ZMQStream based heartbeat.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import time

import zmq
from zmq.eventloop import ioloop


from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import (
    Instance, Float, Bool
)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class Heartbeat(LoggingConfigurable):

    context = Instance('zmq.Context')
    def _context_default(self):
        return zmq.Context.instance()

    loop = Instance('zmq.eventloop.ioloop.IOLoop', allow_none=False)
    def _loop_default(self):
        return ioloop.IOLoop.instance()

    stream = Instance('zmq.eventloop.zmqstream.ZMQStream')

    _beating = Bool(False)
    _kernel_alive = Bool(True)

    time_to_dead = Float(3.0, config=True, help="""Kernel heartbeat interval in seconds.""")
    first_beat = Float(5.0, config=True, help="Delay (in seconds) before sending first heartbeat.")

    def start(self, callback):
        """Start the heartbeating and call the callback if the kernel dies."""
        if not self._beating:
            self._kernel_alive = True

            def ping_or_dead():
                self.stream.flush()
                if self._kernel_alive:
                    self._kernel_alive = False
                    self.stream.send(b'ping')
                    # flush stream to force immediate socket send
                    self.stream.flush()
                else:
                    try:
                        callback()
                    except:
                        pass
                    finally:
                        self.stop()

            def beat_received(msg):
                self._kernel_alive = True

            self.stream.on_recv(beat_received)
            self._hb_periodic_callback = ioloop.PeriodicCallback(
                ping_or_dead, self.time_to_dead*1000, self.loop
            )
            self.loop.add_timeout(time.time()+self.first_beat, self._really_start_hb)
            self._beating= True

    def _really_start_hb(self):
        """callback for delayed heartbeat start

        Only start the hb loop if we haven't been closed during the wait.
        """
        if self._beating and not self.stream.closed():
            self._hb_periodic_callback.start()

    def stop(self):
        """Stop the heartbeating and cancel all related callbacks."""
        if self._beating:
            self._beating = False
            self._hb_periodic_callback.stop()
            if not self.stream.closed():
                self.stream.on_recv(None)

    def pause(self):
        """Pause the heartbeat."""
        pass

    def unpause(self):
        """Unpase the heartbeat."""
        pass
