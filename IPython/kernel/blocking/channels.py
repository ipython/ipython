"""Blocking channels

Useful for test suites and blocking terminal interfaces.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import atexit
import zmq

try:
    from queue import Queue, Empty  # Py 3
except ImportError:
    from Queue import Queue, Empty  # Py 2

from IPython.kernel.channels import IOPubChannel, HBChannel, \
    ShellChannel, StdInChannel, InvalidPortNumber, major_protocol_version
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
    context = None
    session = None
    socket = None
    ioloop = None
    stream = None
    _address = None
    _exiting = False
    proxy_methods = []

    def __init__(self, context, session, address):
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
        self.daemon = True

        self.context = context
        self.session = session
        if isinstance(address, tuple):
            if address[1] == 0:
                message = 'The port number for a channel cannot be 0.'
                raise InvalidPortNumber(message)
            address = "tcp://%s:%i" % address
        self._address = address

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


class BlockingShellChannel(ZMQSocketChannel):
    """The shell channel for issuing request/replies to the kernel."""

    command_queue = None
    # flag for whether execute requests should be allowed to call raw_input:
    allow_stdin = True
    proxy_methods = [
        'execute',
        'complete',
        'inspect',
        'history',
        'kernel_info',
        'shutdown',
        'is_complete',
    ]

    def start(self):
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.linger = 1000
        self.socket.setsockopt(zmq.IDENTITY, self.session.bsession)
        self.socket.connect(self.address)

    def execute(self, code, silent=False, store_history=True,
                user_expressions=None, allow_stdin=None):
        """Execute code in the kernel.

        Parameters
        ----------
        code : str
            A string of Python code.

        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible, and
            will force store_history to be False.

        store_history : bool, optional (default True)
            If set, the kernel will store command history.  This is forced
            to be False if silent is True.

        user_expressions : dict, optional
            A dict mapping names to expressions to be evaluated in the user's
            dict. The expression values are returned as strings formatted using
            :func:`repr`.

        allow_stdin : bool, optional (default self.allow_stdin)
            Flag for whether the kernel can send stdin requests to frontends.

            Some frontends (e.g. the Notebook) do not support stdin requests.
            If raw_input is called from code executed from such a frontend, a
            StdinNotImplementedError will be raised.

        Returns
        -------
        The msg_id of the message sent.
        """
        if user_expressions is None:
            user_expressions = {}
        if allow_stdin is None:
            allow_stdin = self.allow_stdin


        # Don't waste network traffic if inputs are invalid
        if not isinstance(code, string_types):
            raise ValueError('code %r must be a string' % code)
        validate_string_dict(user_expressions)

        # Create class for content/msg creation. Related to, but possibly
        # not in Session.
        content = dict(code=code, silent=silent, store_history=store_history,
                       user_expressions=user_expressions,
                       allow_stdin=allow_stdin,
                       )
        msg = self.session.msg('execute_request', content)
        self._queue_send(msg)
        return msg['header']['msg_id']

    def complete(self, code, cursor_pos=None):
        """Tab complete text in the kernel's namespace.

        Parameters
        ----------
        code : str
            The context in which completion is requested.
            Can be anything between a variable name and an entire cell.
        cursor_pos : int, optional
            The position of the cursor in the block of code where the completion was requested.
            Default: ``len(code)``

        Returns
        -------
        The msg_id of the message sent.
        """
        if cursor_pos is None:
            cursor_pos = len(code)
        content = dict(code=code, cursor_pos=cursor_pos)
        msg = self.session.msg('complete_request', content)
        self._queue_send(msg)
        return msg['header']['msg_id']

    def inspect(self, code, cursor_pos=None, detail_level=0):
        """Get metadata information about an object in the kernel's namespace.

        It is up to the kernel to determine the appropriate object to inspect.

        Parameters
        ----------
        code : str
            The context in which info is requested.
            Can be anything between a variable name and an entire cell.
        cursor_pos : int, optional
            The position of the cursor in the block of code where the info was requested.
            Default: ``len(code)``
        detail_level : int, optional
            The level of detail for the introspection (0-2)

        Returns
        -------
        The msg_id of the message sent.
        """
        if cursor_pos is None:
            cursor_pos = len(code)
        content = dict(code=code, cursor_pos=cursor_pos,
            detail_level=detail_level,
        )
        msg = self.session.msg('inspect_request', content)
        self._queue_send(msg)
        return msg['header']['msg_id']

    def history(self, raw=True, output=False, hist_access_type='range', **kwargs):
        """Get entries from the kernel's history list.

        Parameters
        ----------
        raw : bool
            If True, return the raw input.
        output : bool
            If True, then return the output as well.
        hist_access_type : str
            'range' (fill in session, start and stop params), 'tail' (fill in n)
             or 'search' (fill in pattern param).

        session : int
            For a range request, the session from which to get lines. Session
            numbers are positive integers; negative ones count back from the
            current session.
        start : int
            The first line number of a history range.
        stop : int
            The final (excluded) line number of a history range.

        n : int
            The number of lines of history to get for a tail request.

        pattern : str
            The glob-syntax pattern for a search request.

        Returns
        -------
        The msg_id of the message sent.
        """
        content = dict(raw=raw, output=output, hist_access_type=hist_access_type,
                                                                    **kwargs)
        msg = self.session.msg('history_request', content)
        self._queue_send(msg)
        return msg['header']['msg_id']

    def kernel_info(self):
        """Request kernel info."""
        msg = self.session.msg('kernel_info_request')
        self._queue_send(msg)
        return msg['header']['msg_id']

    def _handle_kernel_info_reply(self, msg):
        """handle kernel info reply

        sets protocol adaptation version
        """
        adapt_version = int(msg['content']['protocol_version'].split('.')[0])
        if adapt_version != major_protocol_version:
            self.session.adapt_version = adapt_version

    def shutdown(self, restart=False):
        """Request an immediate kernel shutdown.

        Upon receipt of the (empty) reply, client code can safely assume that
        the kernel has shut down and it's safe to forcefully terminate it if
        it's still alive.

        The kernel will send the reply via a function registered with Python's
        atexit module, ensuring it's truly done as the kernel is done with all
        normal operation.
        """
        # Send quit message to kernel. Once we implement kernel-side setattr,
        # this should probably be done that way, but for now this will do.
        msg = self.session.msg('shutdown_request', {'restart':restart})
        self._queue_send(msg)
        return msg['header']['msg_id']

    def is_complete(self, code):
        msg = self.session.msg('is_complete_request', {'code': code})
        self._queue_send(msg)
        return msg['header']['msg_id']

    def _recv(self, **kwargs):
        # Listen for kernel_info_reply message to do protocol adaptation
        msg = ZMQSocketChannel._recv(self, **kwargs)
        if msg['msg_type'] == 'kernel_info_reply':
            self._handle_kernel_info_reply(msg)
        return msg


class BlockingIOPubChannel(ZMQSocketChannel):
    """The iopub channel which listens for messages that the kernel publishes.

    This channel is where all output is published to frontends.
    """
    def start(self):
        self.socket = self.context.socket(zmq.SUB)
        self.socket.linger = 1000
        self.socket.setsockopt(zmq.SUBSCRIBE,b'')
        self.socket.setsockopt(zmq.IDENTITY, self.session.bsession)
        self.socket.connect(self.address)


class BlockingStdInChannel(ZMQSocketChannel):
    """The stdin channel to handle raw_input requests that the kernel makes."""
    msg_queue = None
    proxy_methods = ['input']

    def start(self):
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.linger = 1000
        self.socket.setsockopt(zmq.IDENTITY, self.session.bsession)
        self.socket.connect(self.address)

    def input(self, string):
        """Send a string of raw input to the kernel."""
        content = dict(value=string)
        msg = self.session.msg('input_reply', content)
        self._queue_send(msg)


class BlockingHBChannel(HBChannel):

    # This kernel needs quicker monitoring, shorten to 1 sec.
    # less than 0.5s is unreliable, and will get occasional
    # false reports of missed beats.
    time_to_dead = 1.

    def call_handlers(self, since_last_heartbeat):
        """ Pause beating on missed heartbeat. """
        pass
