"""Blocking channels

Useful for test suites and blocking terminal interfaces.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

try:
    from queue import Queue, Empty  # Py 3
except ImportError:
    from Queue import Queue, Empty  # Py 2

from IPython.kernel.channelsabc import ShellChannelABC, IOPubChannelABC, \
    StdInChannelABC
from IPython.kernel.channels import  HBChannel,\
    make_iopub_socket, make_shell_socket, make_stdin_socket,\
    InvalidPortNumber, major_protocol_version
from IPython.utils.py3compat import string_types, iteritems

# some utilities to validate message structure, these might get moved elsewhere
# if they prove to have more generic utility

def validate_string_list(lst):
    """Validate that the input is a list of strings.

    Raises ValueError if not."""
    if not isinstance(lst, list):
        raise ValueError('input %r must be a list' % lst)
    for x in lst:
        if not isinstance(x, string_types):
            raise ValueError('element %r in list must be a string' % x)


def validate_string_dict(dct):
    """Validate that the input is a dict with string keys and values.

    Raises ValueError if not."""
    for k,v in iteritems(dct):
        if not isinstance(k, string_types):
            raise ValueError('key %r in dict must be a string' % k)
        if not isinstance(v, string_types):
            raise ValueError('value %r in dict must be a string' % v)


class ZMQSocketChannel(object):
    """The base class for the channels that use ZMQ sockets."""
    session = None
    socket = None
    stream = None
    _exiting = False
    proxy_methods = []

    def __init__(self, socket, session):
        """Create a channel.

        Parameters
        ----------
        context : :class:`zmq.Context`
            The ZMQ context to use.
        session : :class:`session.Session`
            The session to use.
        address : zmq url
            Standard (ip, port) tuple that the kernel is listening on.
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

    @property
    def address(self):
        """Get the channel's address as a zmq url string.

        These URLS have the form: 'tcp://127.0.0.1:5555'.
        """
        return self._address

    def _queue_send(self, msg):
        """Pass a message to the ZMQ socket to send
        """
        self.session.send(self.socket, msg)

    def start(self):
        pass



class BlockingHBChannel(HBChannel):

    # This kernel needs quicker monitoring, shorten to 1 sec.
    # less than 0.5s is unreliable, and will get occasional
    # false reports of missed beats.
    time_to_dead = 1.

    def call_handlers(self, since_last_heartbeat):
        """ Pause beating on missed heartbeat. """
        pass
