""" Defines a KernelClient that provides signals and slots.
"""
import atexit
import errno
from threading import Thread
import time

import zmq
# import ZMQError in top-level namespace, to avoid ugly attribute-error messages
# during garbage collection of threads at exit:
from zmq import ZMQError
from zmq.eventloop import ioloop, zmqstream

from IPython.external.qt import QtCore

# Local imports
from IPython.utils.traitlets import Type
from IPython.kernel.channels import HBChannel,\
    make_shell_socket, make_iopub_socket, make_stdin_socket
from IPython.kernel import KernelClient

from .kernel_mixins import (QtHBChannelMixin, QtKernelClientMixin)
from .util import SuperQObject

class QtHBChannel(QtHBChannelMixin, HBChannel):
    pass

from IPython.core.release import kernel_protocol_version_info

from IPython.kernel.channelsabc import (
    ShellChannelABC, IOPubChannelABC, StdInChannelABC,
)
from IPython.utils.py3compat import string_types, iteritems

major_protocol_version = kernel_protocol_version_info[0]

class InvalidPortNumber(Exception):
    pass

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



class QtZMQSocketChannel(SuperQObject, Thread):
    """The base class for the channels that use ZMQ sockets."""
    session = None
    socket = None
    ioloop = None
    stream = None
    _exiting = False
    proxy_methods = []

    # Emitted when the channel is started.
    started = QtCore.Signal()

    # Emitted when the channel is stopped.
    stopped = QtCore.Signal()

    message_received = QtCore.Signal(object)

    #---------------------------------------------------------------------------
    # InProcessChannel interface
    #---------------------------------------------------------------------------

    def call_handlers_later(self, *args, **kwds):
        """ Call the message handlers later.
        """
        do_later = lambda: self.call_handlers(*args, **kwds)
        QtCore.QTimer.singleShot(0, do_later)

    def process_events(self):
        """ Process any pending GUI events.
        """
        QtCore.QCoreApplication.instance().processEvents()

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
        super(QtZMQSocketChannel, self).__init__()
        self.daemon = True

        self.socket = socket
        self.session = session
        atexit.register(self._notice_exit)

    def _notice_exit(self):
        self._exiting = True

    def _run_loop(self):
        """Run my loop, ignoring EINTR events in the poller"""
        while True:
            try:
                self.ioloop.start()
            except ZMQError as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise
            except Exception:
                if self._exiting:
                    break
                else:
                    raise
            else:
                break

    def start(self):
        """ Reimplemented to emit signal.
        """
        super(QtZMQSocketChannel, self).start()
        self.started.emit()

    def stop(self):
        """Stop the channel's event loop and join its thread.

        This calls :meth:`~threading.Thread.join` and returns when the thread
        terminates. :class:`RuntimeError` will be raised if
        :meth:`~threading.Thread.start` is called again.
        """
        if self.ioloop is not None:
            self.ioloop.stop()
        self.join()
        self.close()
        self.stopped.emit()

    def close(self):
        if self.ioloop is not None:
            try:
                self.ioloop.close(all_fds=True)
            except Exception:
                pass
        if self.socket is not None:
            try:
                self.socket.close(linger=0)
            except Exception:
                pass
            self.socket = None

    @property
    def address(self):
        """Get the channel's address as a zmq url string.

        These URLS have the form: 'tcp://127.0.0.1:5555'.
        """
        return self._address

    def _queue_send(self, msg):
        """Queue a message to be sent from the IOLoop's thread.

        Parameters
        ----------
        msg : message to send

        This is threadsafe, as it uses IOLoop.add_callback to give the loop's
        thread control of the action.
        """
        def thread_send():
            self.session.send(self.stream, msg)
        self.ioloop.add_callback(thread_send)

    def _handle_recv(self, msg):
        """Callback for stream.on_recv.

        Unpacks message, and calls handlers with it.
        """
        ident,smsg = self.session.feed_identities(msg)
        msg = self.session.deserialize(smsg)
        self.call_handlers(msg)

    def call_handlers(self, msg):
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application level
        handlers are called in the application thread.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)


class QtShellChannel(QtZMQSocketChannel):
    """The shell channel for issuing request/replies to the kernel."""

    # Emitted when a reply has been received for the corresponding request type.
    execute_reply = QtCore.Signal(object)
    complete_reply = QtCore.Signal(object)
    inspect_reply = QtCore.Signal(object)
    history_reply = QtCore.Signal(object)
    kernel_info_reply = QtCore.Signal(object)

    def __init__(self, socket, session):
        super(QtShellChannel, self).__init__(socket, session)
        self.ioloop = ioloop.IOLoop()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.stream = zmqstream.ZMQStream(self.socket, self.ioloop)
        self.stream.on_recv(self._handle_recv)
        self._run_loop()

    def call_handlers(self, msg):
        super(QtShellChannel, self).call_handlers(msg)

        # Catch kernel_info_reply for message spec adaptation
        msg_type = msg['header']['msg_type']
        if msg_type == 'kernel_info_reply':
            self._handle_kernel_info_reply(msg)

        # Emit specific signals
        signal = getattr(self, msg_type, None)
        if signal:
            signal.emit(msg)

    def _handle_kernel_info_reply(self, msg):
        """handle kernel info reply

        sets protocol adaptation version
        """
        adapt_version = int(msg['content']['protocol_version'].split('.')[0])
        if adapt_version != major_protocol_version:
            self.session.adapt_version = adapt_version


class QtIOPubChannel(QtZMQSocketChannel):
    """The iopub channel which listens for messages that the kernel publishes.

    This channel is where all output is published to frontends.
    """
    # Emitted when a message of type 'stream' is received.
    stream_received = QtCore.Signal(object)

    # Emitted when a message of type 'execute_input' is received.
    execute_input_received = QtCore.Signal(object)

    # Emitted when a message of type 'execute_result' is received.
    execute_result_received = QtCore.Signal(object)

    # Emitted when a message of type 'error' is received.
    error_received = QtCore.Signal(object)

    # Emitted when a message of type 'display_data' is received
    display_data_received = QtCore.Signal(object)

    # Emitted when a crash report message is received from the kernel's
    # last-resort sys.excepthook.
    crash_received = QtCore.Signal(object)

    # Emitted when a shutdown is noticed.
    shutdown_reply_received = QtCore.Signal(object)

    def __init__(self, socket, session):
        super(QtIOPubChannel, self).__init__(socket, session)
        self.ioloop = ioloop.IOLoop()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.stream = zmqstream.ZMQStream(self.socket, self.ioloop)
        self.stream.on_recv(self._handle_recv)
        self._run_loop()

    def call_handlers(self, msg):
        super(QtIOPubChannel, self).call_handlers(msg)

        # Emit signals for specialized message types.
        msg_type = msg['header']['msg_type']
        signal = getattr(self, msg_type + '_received', None)
        if signal:
            signal.emit(msg)

    def flush(self, timeout=1.0):
        """Immediately processes all pending messages on the iopub channel.

        Callers should use this method to ensure that :meth:`call_handlers`
        has been called for all messages that have been received on the
        0MQ SUB socket of this channel.

        This method is thread safe.

        Parameters
        ----------
        timeout : float, optional
            The maximum amount of time to spend flushing, in seconds. The
            default is one second.
        """
        # We do the IOLoop callback process twice to ensure that the IOLoop
        # gets to perform at least one full poll.
        stop_time = time.time() + timeout
        for i in range(2):
            self._flushed = False
            self.ioloop.add_callback(self._flush)
            while not self._flushed and time.time() < stop_time:
                time.sleep(0.01)

    def _flush(self):
        """Callback for :method:`self.flush`."""
        self.stream.flush()
        self._flushed = True


class QtStdInChannel(QtZMQSocketChannel):
    """The stdin channel to handle raw_input requests that the kernel makes."""

    msg_queue = None
    proxy_methods = ['input']

    # Emitted when an input request is received.
    input_requested = QtCore.Signal(object)

    def __init__(self, socket, session):
        super(QtStdInChannel, self).__init__(socket, session)
        self.ioloop = ioloop.IOLoop()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.stream = zmqstream.ZMQStream(self.socket, self.ioloop)
        self.stream.on_recv(self._handle_recv)
        self._run_loop()

    def call_handlers(self, msg):
        super(QtStdInChannel, self).call_handlers(msg)

        # Emit signals for specialized message types.
        msg_type = msg['header']['msg_type']
        if msg_type == 'input_request':
            self.input_requested.emit(msg)


ShellChannelABC.register(QtShellChannel)
IOPubChannelABC.register(QtIOPubChannel)
StdInChannelABC.register(QtStdInChannel)


class QtKernelClient(QtKernelClientMixin, KernelClient):
    """ A KernelClient that provides signals and slots.
    """
    def start_channels(self, shell=True, iopub=True, stdin=True, hb=True):
        if shell:
            self.shell_channel.kernel_info_reply.connect(self._handle_kernel_info_reply)
        super(QtKernelClient, self).start_channels(shell, iopub, stdin, hb)

    def _handle_kernel_info_reply(self, msg):
        super(QtKernelClient, self)._handle_kernel_info_reply(msg)
        self.shell_channel.kernel_info_reply.disconnect(self._handle_kernel_info_reply)

    iopub_channel_class = Type(QtIOPubChannel)
    shell_channel_class = Type(QtShellChannel)
    stdin_channel_class = Type(QtStdInChannel)
    hb_channel_class = Type(QtHBChannel)
