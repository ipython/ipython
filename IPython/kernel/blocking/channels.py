"""Blocking channels

Useful for test suites and blocking terminal interfaces.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

try:
    from queue import Queue, Empty  # Py 3
except ImportError:
    from Queue import Queue, Empty  # Py 2

from IPython.utils.py3compat import string_types, iteritems

# some utilities to validate message structure, these might get moved elsewhere
# if they prove to have more generic utility

def validate_string_dict(dct):
    """Validate that the input is a dict with string keys and values.

    Raises ValueError if not."""
    for k,v in iteritems(dct):
        if not isinstance(k, string_types):
            raise ValueError('key %r in dict must be a string' % k)
        if not isinstance(v, string_types):
            raise ValueError('value %r in dict must be a string' % v)


class ZMQSocketChannel(object):
    """A ZMQ socket in a simple blocking API"""
    session = None
    socket = None
    stream = None
    _exiting = False
    proxy_methods = []

    def __init__(self, socket, session, loop=None):
        """Create a channel.

        Parameters
        ----------
        socket : :class:`zmq.Socket`
            The ZMQ socket to use.
        session : :class:`session.Session`
            The session to use.
        loop
            Unused here, for other implementations
        """
        super(ZMQSocketChannel, self).__init__()

        self.socket = socket
        self.session = session

    def _recv(self, **kwargs):
        msg = self.socket.recv_multipart(**kwargs)
        ident,smsg = self.session.feed_identities(msg)
        return self.session.deserialize(smsg)

    def get_msg(self, block=True, timeout=None):
        """ Gets a message if there is one that is ready. """
        if block:
            if timeout is not None:
                timeout *= 1000  # seconds to ms
            ready = self.socket.poll(timeout)
        else:
            ready = self.socket.poll(timeout=0)

        if ready:
            return self._recv()
        else:
            raise Empty

    def get_msgs(self):
        """ Get all messages that are currently ready. """
        msgs = []
        while True:
            try:
                msgs.append(self.get_msg(block=False))
            except Empty:
                break
        return msgs

    def msg_ready(self):
        """ Is there a message that has been received? """
        return bool(self.socket.poll(timeout=0))

    def close(self):
        if self.socket is not None:
            try:
                self.socket.close(linger=0)
            except Exception:
                pass
            self.socket = None
    stop =  close

    def is_alive(self):
        return (self.socket is not None)

    def _queue_send(self, msg):
        """Pass a message to the ZMQ socket to send
        """
        self.session.send(self.socket, msg)

    def start(self):
        pass

