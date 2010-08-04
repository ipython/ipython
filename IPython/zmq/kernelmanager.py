"""Classes to manage the interaction with a running kernel.

Todo
====

* Create logger to handle debugging and console messages.
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

# Standard library imports.
from Queue import Queue, Empty
from subprocess import Popen
from threading import Thread
import time

# System library imports.
import zmq
from zmq import POLLIN, POLLOUT, POLLERR
from zmq.eventloop import ioloop

# Local imports.
from IPython.utils.traitlets import HasTraits, Any, Instance, Type
from kernel import launch_kernel
from session import Session

#-----------------------------------------------------------------------------
# Constants and exceptions
#-----------------------------------------------------------------------------

LOCALHOST = '127.0.0.1'

class InvalidPortNumber(Exception):
    pass

#-----------------------------------------------------------------------------
# ZMQ Socket Channel classes
#-----------------------------------------------------------------------------

class ZmqSocketChannel(Thread):
    """The base class for the channels that use ZMQ sockets.
    """
    context = None
    session = None
    socket = None
    ioloop = None
    iostate = None
    _address = None

    def __init__(self, context, session, address):
        """Create a channel

        Parameters
        ----------
        context : zmq.Context
            The ZMQ context to use.
        session : session.Session
            The session to use.
        address : tuple
            Standard (ip, port) tuple that the kernel is listening on.
        """
        super(ZmqSocketChannel, self).__init__()
        self.daemon = True

        self.context = context
        self.session = session
        if address[1] == 0:
            message = 'The port number for a channel cannot be 0.'
            raise InvalidPortNumber(message)
        self._address = address

    def stop(self):
        """Stop the channel's activity.

        This calls :method:`Thread.join` and returns when the thread
        terminates. :class:`RuntimeError` will be raised if 
        :method:`self.start` is called again.
        """
        self.join()

    @property
    def address(self):
        """Get the channel's address as an (ip, port) tuple.
        
        By the default, the address is (localhost, 0), where 0 means a random
        port.
        """
        return self._address

    def add_io_state(self, state):
        """Add IO state to the eventloop.

        Parameters
        ----------
        state : zmq.POLLIN|zmq.POLLOUT|zmq.POLLERR
            The IO state flag to set.

        This is thread safe as it uses the thread safe IOLoop.add_callback.
        """
        def add_io_state_callback():
            if not self.iostate & state:
                self.iostate = self.iostate | state
                self.ioloop.update_handler(self.socket, self.iostate)
        self.ioloop.add_callback(add_io_state_callback)

    def drop_io_state(self, state):
        """Drop IO state from the eventloop.

        Parameters
        ----------
        state : zmq.POLLIN|zmq.POLLOUT|zmq.POLLERR
            The IO state flag to set.

        This is thread safe as it uses the thread safe IOLoop.add_callback.
        """
        def drop_io_state_callback():
            if self.iostate & state:
                self.iostate = self.iostate & (~state)
                self.ioloop.update_handler(self.socket, self.iostate)
        self.ioloop.add_callback(drop_io_state_callback)


class XReqSocketChannel(ZmqSocketChannel):
    """The XREQ channel for issues request/replies to the kernel.
    """

    command_queue = None

    def __init__(self, context, session, address):
        self.command_queue = Queue()
        super(XReqSocketChannel, self).__init__(context, session, address)

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.socket = self.context.socket(zmq.XREQ)
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.address)
        self.ioloop = ioloop.IOLoop()
        self.iostate = POLLERR|POLLIN
        self.ioloop.add_handler(self.socket, self._handle_events, 
                                self.iostate)
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()
        super(XReqSocketChannel, self).stop()

    def call_handlers(self, msg):
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application leve
        handlers are called in the application thread.
        """
        raise NotImplementedError('call_handlers must be defined in a subclass.')

    def execute(self, code):
        """Execute code in the kernel.

        Parameters
        ----------
        code : str
            A string of Python code.

        Returns
        -------
        The msg_id of the message sent.
        """
        # Create class for content/msg creation. Related to, but possibly
        # not in Session.
        content = dict(code=code)
        msg = self.session.msg('execute_request', content)
        self._queue_request(msg)
        return msg['header']['msg_id']

    def complete(self, text, line, block=None):
        """Tab complete text, line, block in the kernel's namespace.

        Parameters
        ----------
        text : str
            The text to complete.
        line : str
            The full line of text that is the surrounding context for the 
            text to complete.
        block : str
            The full block of code in which the completion is being requested.

        Returns
        -------
        The msg_id of the message sent.

        """
        content = dict(text=text, line=line)
        msg = self.session.msg('complete_request', content)
        self._queue_request(msg)
        return msg['header']['msg_id']

    def object_info(self, oname):
        """Get metadata information about an object.

        Parameters
        ----------
        oname : str
            A string specifying the object name.
        
        Returns
        -------
        The msg_id of the message sent.
        """
        content = dict(oname=oname)
        msg = self.session.msg('object_info_request', content)
        self._queue_request(msg)
        return msg['header']['msg_id']

    def _handle_events(self, socket, events):
        if events & POLLERR:
            self._handle_err()
        if events & POLLOUT:
            self._handle_send()
        if events & POLLIN:
            self._handle_recv()

    def _handle_recv(self):
        msg = self.socket.recv_json()
        self.call_handlers(msg)

    def _handle_send(self):
        try:
            msg = self.command_queue.get(False)
        except Empty:
            pass
        else:
            self.socket.send_json(msg)
        if self.command_queue.empty():
            self.drop_io_state(POLLOUT)

    def _handle_err(self):
        # We don't want to let this go silently, so eventually we should log.
        raise zmq.ZMQError()

    def _queue_request(self, msg):
        self.command_queue.put(msg)
        self.add_io_state(POLLOUT)


class SubSocketChannel(ZmqSocketChannel):
    """The SUB channel which listens for messages that the kernel publishes.
    """

    def __init__(self, context, session, address):
        super(SubSocketChannel, self).__init__(context, session, address)

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE,'')
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.address)
        self.ioloop = ioloop.IOLoop()
        self.iostate = POLLIN|POLLERR
        self.ioloop.add_handler(self.socket, self._handle_events, 
                                self.iostate)
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()
        super(SubSocketChannel, self).stop()

    def call_handlers(self, msg):
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application leve
        handlers are called in the application thread.
        """
        raise NotImplementedError('call_handlers must be defined in a subclass.')

    def flush(self, timeout=1.0):
        """Immediately processes all pending messages on the SUB channel.

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
        for i in xrange(2):
            self._flushed = False
            self.ioloop.add_callback(self._flush)
            while not self._flushed and time.time() < stop_time:
                time.sleep(0.01)

    def _handle_events(self, socket, events):
        # Turn on and off POLLOUT depending on if we have made a request
        if events & POLLERR:
            self._handle_err()
        if events & POLLIN:
            self._handle_recv()

    def _handle_err(self):
        # We don't want to let this go silently, so eventually we should log.
        raise zmq.ZMQError()

    def _handle_recv(self):
        # Get all of the messages we can
        while True:
            try:
                msg = self.socket.recv_json(zmq.NOBLOCK)
            except zmq.ZMQError:
                # Check the errno?
                # Will this tigger POLLERR?
                break
            else:
                self.call_handlers(msg)

    def _flush(self):
        """Callback for :method:`self.flush`."""
        self._flushed = True


class RepSocketChannel(ZmqSocketChannel):
    """A reply channel to handle raw_input requests that the kernel makes."""

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.ioloop = ioloop.IOLoop()
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()
        super(RepSocketChannel, self).stop()

    def on_raw_input(self):
        pass


#-----------------------------------------------------------------------------
# Main kernel manager class
#-----------------------------------------------------------------------------


class KernelManager(HasTraits):
    """ Manages a kernel for a frontend.

    The SUB channel is for the frontend to receive messages published by the
    kernel.
        
    The REQ channel is for the frontend to make requests of the kernel.
    
    The REP channel is for the kernel to request stdin (raw_input) from the
    frontend.
    """
    # The PyZMQ Context to use for communication with the kernel.
    context = Instance(zmq.Context)

    # The Session to use for communication with the kernel.
    session = Instance(Session)

    # The classes to use for the various channels.
    xreq_channel_class = Type(XReqSocketChannel)
    sub_channel_class = Type(SubSocketChannel)
    rep_channel_class = Type(RepSocketChannel)
    
    # Protected traits.
    _kernel = Instance(Popen)
    _xreq_address = Any
    _sub_address = Any
    _rep_address = Any
    _xreq_channel = Any
    _sub_channel = Any
    _rep_channel = Any

    def __init__(self, xreq_address=None, sub_address=None, rep_address=None,
                 context=None, session=None):
        self._xreq_address = (LOCALHOST, 0) if xreq_address is None else xreq_address
        self._sub_address = (LOCALHOST, 0) if sub_address is None else sub_address
        self._rep_address = (LOCALHOST, 0) if rep_address is None else rep_address
        self.context = zmq.Context() if context is None else context
        self.session = Session() if session is None else session

    #--------------------------------------------------------------------------
    # Channel management methods:
    #--------------------------------------------------------------------------

    def start_channels(self):
        """Starts the channels for this kernel.

        This will create the channels if they do not exist and then start
        them. If port numbers of 0 are being used (random ports) then you
        must first call :method:`start_kernel`. If the channels have been
        stopped and you call this, :class:`RuntimeError` will be raised.
        """
        self.xreq_channel.start()
        self.sub_channel.start()
        self.rep_channel.start()

    def stop_channels(self):
        """Stops the channels for this kernel.

        This stops the channels by joining their threads. If the channels
        were not started, :class:`RuntimeError` will be raised.
        """
        self.xreq_channel.stop()
        self.sub_channel.stop()
        self.rep_channel.stop()

    @property
    def channels_running(self):
        """Are all of the channels created and running?"""
        return self.xreq_channel.is_alive() \
            and self.sub_channel.is_alive() \
            and self.rep_channel.is_alive()

    #--------------------------------------------------------------------------
    # Kernel process management methods:
    #--------------------------------------------------------------------------

    def start_kernel(self):
        """Starts a kernel process and configures the manager to use it.

        If random ports (port=0) are being used, this method must be called
        before the channels are created.
        """
        xreq, sub, rep = self.xreq_address, self.sub_address, self.rep_address
        if xreq[0] != LOCALHOST or sub[0] != LOCALHOST or rep[0] != LOCALHOST:
            raise RuntimeError("Can only launch a kernel on localhost."
                               "Make sure that the '*_address' attributes are "
                               "configured properly.")

        kernel, xrep, pub, req = launch_kernel(
            xrep_port=xreq[1], pub_port=sub[1], req_port=rep[1])
        self._kernel = kernel
        self._xreq_address = (LOCALHOST, xrep)
        self._sub_address = (LOCALHOST, pub)
        self._rep_address = (LOCALHOST, req)

    @property
    def has_kernel(self):
        """Returns whether a kernel process has been specified for the kernel
        manager.

        A kernel process can be set via 'start_kernel' or 'set_kernel'.
        """
        return self._kernel is not None

    def kill_kernel(self):
        """ Kill the running kernel. """
        if self._kernel is not None:
            self._kernel.kill()
            self._kernel = None
        else:
            raise RuntimeError("Cannot kill kernel. No kernel is running!")

    def signal_kernel(self, signum):
        """ Sends a signal to the kernel. """
        if self._kernel is not None:
            self._kernel.send_signal(signum)
        else:
            raise RuntimeError("Cannot signal kernel. No kernel is running!")

    @property
    def is_alive(self):
        """Is the kernel process still running?"""
        if self._kernel is not None:
            if self._kernel.poll() is None:
                return True
            else:
                return False
        else:
            # We didn't start the kernel with this KernelManager so we don't
            # know if it is running. We should use a heartbeat for this case.
            return True

    #--------------------------------------------------------------------------
    # Channels used for communication with the kernel:
    #--------------------------------------------------------------------------

    @property
    def xreq_channel(self):
        """Get the REQ socket channel object to make requests of the kernel."""
        if self._xreq_channel is None:
            self._xreq_channel = self.xreq_channel_class(self.context, 
                                                         self.session,
                                                         self.xreq_address)
        return self._xreq_channel

    @property
    def sub_channel(self):
        """Get the SUB socket channel object."""
        if self._sub_channel is None:
            self._sub_channel = self.sub_channel_class(self.context,
                                                       self.session,
                                                       self.sub_address)
        return self._sub_channel

    @property
    def rep_channel(self):
        """Get the REP socket channel object to handle stdin (raw_input)."""
        if self._rep_channel is None:
            self._rep_channel = self.rep_channel_class(self.context, 
                                                       self.session,
                                                       self.rep_address)
        return self._rep_channel

    @property
    def xreq_address(self):
        return self._xreq_address

    @property
    def sub_address(self):
        return self._sub_address

    @property
    def rep_address(self):
        return self._rep_address

    
