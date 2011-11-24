"""The client and server for a basic ping-pong style heartbeat.
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

import socket
import sys
from threading import Thread

import zmq

from IPython.utils.localinterfaces import LOCALHOST

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class Heartbeat(Thread):
    "A simple ping-pong style heartbeat that runs in a thread."

    def __init__(self, context, addr=(LOCALHOST, 0)):
        Thread.__init__(self)
        self.context = context
        self.ip, self.port = addr
        if self.port == 0:
            s = socket.socket()
            # '*' means all interfaces to 0MQ, which is '' to socket.socket
            s.bind(('' if self.ip == '*' else self.ip, 0))
            self.port = s.getsockname()[1]
            s.close()
        self.addr = (self.ip, self.port)
        self.daemon = True

    def run(self):
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind('tcp://%s:%i' % self.addr)
        zmq.device(zmq.FORWARDER, self.socket, self.socket)

