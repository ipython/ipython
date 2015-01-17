"""Base class to manage the interaction with a running kernel"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import
from IPython.kernel.channels import major_protocol_version
from IPython.utils.py3compat import string_types, iteritems

import zmq

from IPython.utils.traitlets import (
    Any, Instance, Type,
)

from .channelsabc import (ChannelABC, HBChannelABC)
from .clientabc import KernelClientABC
from .connect import ConnectionFileMixin


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


class KernelClient(ConnectionFileMixin):
    """Communicates with a single kernel on any host via zmq channels.

    There are four channels associated with each kernel:

    * shell: for request/reply calls to the kernel.
    * iopub: for the kernel to publish results to frontends.
    * hb: for monitoring the kernel's heartbeat.
    * stdin: for frontends to reply to raw_input calls in the kernel.

    The methods of the channels are exposed as methods of the client itself
    (KernelClient.execute, complete, history, etc.).
    See the channels themselves for documentation of these methods.

    """

    # The PyZMQ Context to use for communication with the kernel.
    context = Instance(zmq.Context)
    def _context_default(self):
        return zmq.Context.instance()

    # The classes to use for the various channels
    shell_channel_class = Type(ChannelABC)
    iopub_channel_class = Type(ChannelABC)
    stdin_channel_class = Type(ChannelABC)
    hb_channel_class = Type(HBChannelABC)

    # Protected traits
    _shell_channel = Any
    _iopub_channel = Any
    _stdin_channel = Any
    _hb_channel = Any

    # flag for whether execute requests should be allowed to call raw_input:
    allow_stdin = True

    #--------------------------------------------------------------------------
    # Channel proxy methods
    #--------------------------------------------------------------------------

    def _get_msg(channel, *args, **kwargs):
        return channel.get_msg(*args, **kwargs)

    def get_shell_msg(self, *args, **kwargs):
        """Get a message from the shell channel"""
        return self.shell_channel.get_msg(*args, **kwargs)

    def get_iopub_msg(self, *args, **kwargs):
        """Get a message from the iopub channel"""
        return self.iopub_channel.get_msg(*args, **kwargs)

    def get_stdin_msg(self, *args, **kwargs):
        """Get a message from the stdin channel"""
        return self.stdin_channel.get_msg(*args, **kwargs)

    #--------------------------------------------------------------------------
    # Channel management methods
    #--------------------------------------------------------------------------

    def start_channels(self, shell=True, iopub=True, stdin=True, hb=True):
        """Starts the channels for this kernel.

        This will create the channels if they do not exist and then start
        them (their activity runs in a thread). If port numbers of 0 are
        being used (random ports) then you must first call
        :meth:`start_kernel`. If the channels have been stopped and you
        call this, :class:`RuntimeError` will be raised.
        """
        if shell:
            self.shell_channel.start()
            self.kernel_info()
        if iopub:
            self.iopub_channel.start()
        if stdin:
            self.stdin_channel.start()
            self.allow_stdin = True
        else:
            self.allow_stdin = False
        if hb:
            self.hb_channel.start()

    def stop_channels(self):
        """Stops all the running channels for this kernel.

        This stops their event loops and joins their threads.
        """
        if self.shell_channel.is_alive():
            self.shell_channel.stop()
        if self.iopub_channel.is_alive():
            self.iopub_channel.stop()
        if self.stdin_channel.is_alive():
            self.stdin_channel.stop()
        if self.hb_channel.is_alive():
            self.hb_channel.stop()

    @property
    def channels_running(self):
        """Are any of the channels created and running?"""
        return (self.shell_channel.is_alive() or self.iopub_channel.is_alive() or
                self.stdin_channel.is_alive() or self.hb_channel.is_alive())

    ioloop = None  # Overridden in subclasses that use pyzmq event loop

    @property
    def shell_channel(self):
        """Get the shell channel object for this kernel."""
        if self._shell_channel is None:
            url = self._make_url('shell')
            self.log.debug("connecting shell channel to %s", url)
            socket = self.connect_shell(identity=self.session.bsession)
            self._shell_channel = self.shell_channel_class(
                socket, self.session, self.ioloop
            )
        return self._shell_channel

    @property
    def iopub_channel(self):
        """Get the iopub channel object for this kernel."""
        if self._iopub_channel is None:
            url = self._make_url('iopub')
            self.log.debug("connecting iopub channel to %s", url)
            socket = self.connect_iopub()
            self._iopub_channel = self.iopub_channel_class(
                socket, self.session, self.ioloop
            )
        return self._iopub_channel

    @property
    def stdin_channel(self):
        """Get the stdin channel object for this kernel."""
        if self._stdin_channel is None:
            url = self._make_url('stdin')
            self.log.debug("connecting stdin channel to %s", url)
            socket = self.connect_stdin(identity=self.session.bsession)
            self._stdin_channel = self.stdin_channel_class(
                socket, self.session, self.ioloop
            )
        return self._stdin_channel

    @property
    def hb_channel(self):
        """Get the hb channel object for this kernel."""
        if self._hb_channel is None:
            url = self._make_url('hb')
            self.log.debug("connecting heartbeat channel to %s", url)
            self._hb_channel = self.hb_channel_class(
                self.context, self.session, url
            )
        return self._hb_channel

    def is_alive(self):
        """Is the kernel process still running?"""
        if self._hb_channel is not None:
            # We didn't start the kernel with this KernelManager so we
            # use the heartbeat.
            return self._hb_channel.is_beating()
        else:
            # no heartbeat and not local, we can't tell if it's running,
            # so naively return True
            return True


    # Methods to send specific messages on channels
    def execute(self, code, silent=False, store_history=True,
                user_expressions=None, allow_stdin=None, stop_on_error=True):
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

        stop_on_error: bool, optional (default True)
            Flag whether to abort the execution queue, if an exception is encountered.

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
                       allow_stdin=allow_stdin, stop_on_error=stop_on_error
                       )
        msg = self.session.msg('execute_request', content)
        self.shell_channel.send(msg)
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
        self.shell_channel.send(msg)
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
        self.shell_channel.send(msg)
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
        self.shell_channel.send(msg)
        return msg['header']['msg_id']

    def kernel_info(self):
        """Request kernel info."""
        msg = self.session.msg('kernel_info_request')
        self.shell_channel.send(msg)
        return msg['header']['msg_id']

    def _handle_kernel_info_reply(self, msg):
        """handle kernel info reply

        sets protocol adaptation version. This might
        be run from a separate thread.
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
        self.shell_channel.send(msg)
        return msg['header']['msg_id']

    def is_complete(self, code):
        msg = self.session.msg('is_complete_request', {'code': code})
        self.shell_channel.send(msg)
        return msg['header']['msg_id']

    def input(self, string):
        """Send a string of raw input to the kernel."""
        content = dict(value=string)
        msg = self.session.msg('input_reply', content)
        self.stdin_channel.send(msg)


KernelClientABC.register(KernelClient)
