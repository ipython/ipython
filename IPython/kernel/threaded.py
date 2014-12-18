""" Defines a KernelClient that provides thread-safe sockets with async callbacks on message replies.
"""
from __future__ import absolute_import
import atexit
import errno
from threading import Thread
import time

import zmq
# import ZMQError in top-level namespace, to avoid ugly attribute-error messages
# during garbage collection of threads at exit:
from zmq import ZMQError
from zmq.eventloop import ioloop, zmqstream

# Local imports
from IPython.utils.traitlets import Type, Instance
from IPython.kernel.channels import HBChannel
from IPython.kernel import KernelClient
from IPython.kernel.channels import HBChannel

class ThreadedZMQSocketChannel(object):
    """A ZMQ socket invoking a callback in the ioloop"""
    session = None
    socket = None
    ioloop = None
    stream = None
    _inspect = None

    def __init__(self, socket, session, loop):
        """Create a channel.

        Parameters
        ----------
        socket : :class:`zmq.Socket`
            The ZMQ socket to use.
        session : :class:`session.Session`
            The session to use.
        loop
            A pyzmq ioloop to connect the socket to using a ZMQStream
        """
        super(ThreadedZMQSocketChannel, self).__init__()

        self.socket = socket
        self.session = session
        self.ioloop = loop

        self.stream = zmqstream.ZMQStream(self.socket, self.ioloop)
        self.stream.on_recv(self._handle_recv)

    _is_alive = False
    def is_alive(self):
        return self._is_alive

    def start(self):
        self._is_alive = True

    def stop(self):
        self._is_alive = False

    def close(self):
        if self.socket is not None:
            try:
                self.socket.close(linger=0)
            except Exception:
                pass
            self.socket = None

    def send(self, msg):
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
        # let client inspect messages
        if self._inspect:
            self._inspect(msg)
        self.call_handlers(msg)

    def call_handlers(self, msg):
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application level
        handlers are called in the application thread.
        """
        pass

    def process_events(self):
        """Subclasses should override this with a method
        processing any pending GUI events.
        """
        pass


    def flush(self, timeout=1.0):
        """Immediately processes all pending messages on this channel.

        This is only used for the IOPub channel.

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


class IOLoopThread(Thread):
    """Run a pyzmq ioloop in a thread to send and receive messages
    """
    def __init__(self, loop):
        super(IOLoopThread, self).__init__()
        self.daemon = True
        atexit.register(self._notice_exit)
        self.ioloop = loop or ioloop.IOLoop()

    def _notice_exit(self):
        self._exiting = True

    def run(self):
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

    def close(self):
        if self.ioloop is not None:
            try:
                self.ioloop.close(all_fds=True)
            except Exception:
                pass


class ThreadedKernelClient(KernelClient):
    """ A KernelClient that provides thread-safe sockets with async callbacks on message replies.
    """

    _ioloop = None
    @property
    def ioloop(self):
        if self._ioloop is None:
            self._ioloop = ioloop.IOLoop()
        return self._ioloop

    ioloop_thread = Instance(IOLoopThread)

    def start_channels(self, shell=True, iopub=True, stdin=True, hb=True):
        if shell:
            self.shell_channel._inspect = self._check_kernel_info_reply

        self.ioloop_thread = IOLoopThread(self.ioloop)
        self.ioloop_thread.start()

        super(ThreadedKernelClient, self).start_channels(shell, iopub, stdin, hb)

    def _check_kernel_info_reply(self, msg):
        """This is run in the ioloop thread when the kernel info reply is recieved
        """
        if msg['msg_type'] == 'kernel_info_reply':
            self._handle_kernel_info_reply(msg)
            self.shell_channel._inspect = None

    def stop_channels(self):
        super(ThreadedKernelClient, self).stop_channels()
        if self.ioloop_thread.is_alive():
            self.ioloop_thread.stop()

    iopub_channel_class = Type(ThreadedZMQSocketChannel)
    shell_channel_class = Type(ThreadedZMQSocketChannel)
    stdin_channel_class = Type(ThreadedZMQSocketChannel)
    hb_channel_class = Type(HBChannel)
