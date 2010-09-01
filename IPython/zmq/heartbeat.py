"""The client and server for a basic ping-pong style heartbeat.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
from threading import Thread

import zmq

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class Heartbeat(Thread):
    "A simple ping-pong style heartbeat that runs in a thread."

    def __init__(self, context, addr=('127.0.0.1', 0)):
        Thread.__init__(self)
        self.context = context
        self.addr = addr
        self.ip = addr[0]
        self.port = addr[1]
        self.daemon = True

    def run(self):
        self.socket = self.context.socket(zmq.REP)
        if self.port == 0:
            self.port = self.socket.bind_to_random_port('tcp://%s' % self.ip)
        else:
            self.socket.bind('tcp://%s:%i' % self.addr)
        zmq.device(zmq.FORWARDER, self.socket, self.socket)

