"""Utility for forwarding file read events over a zmq socket.

This is necessary because select on Windows only supports sockets, not FDs.

Authors:

* MinRK

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import uuid
import zmq

from threading import Thread

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class ForwarderThread(Thread):
    def __init__(self, sock, fd):
        Thread.__init__(self)
        self.daemon=True
        self.sock = sock
        self.fd = fd

    def run(self):
        """Loop through lines in self.fd, and send them over self.sock."""
        line = self.fd.readline()
        # allow for files opened in unicode mode
        if isinstance(line, unicode):
            send = self.sock.send_unicode
        else:
            send = self.sock.send
        while line:
            send(line)
            line = self.fd.readline()
        # line == '' means EOF
        self.fd.close()
        self.sock.close()

def forward_read_events(fd, context=None):
    """Forward read events from an FD over a socket.

    This method wraps a file in a socket pair, so it can
    be polled for read events by select (specifically zmq.eventloop.ioloop)
    """
    if context is None:
        context = zmq.Context.instance()
    push = context.socket(zmq.PUSH)
    push.setsockopt(zmq.LINGER, -1)
    pull = context.socket(zmq.PULL)
    addr='inproc://%s'%uuid.uuid4()
    push.bind(addr)
    pull.connect(addr)
    forwarder = ForwarderThread(push, fd)
    forwarder.start()
    return pull


__all__ = ['forward_read_events']
