"""Kernel frontend classes.

TODO: Create logger to handle debugging and console messages.

"""

# Standard library imports.
from Queue import Queue, Empty
from subprocess import Popen
from threading import Thread
import time
import traceback

# System library imports.
import zmq
from zmq import POLLIN, POLLOUT, POLLERR
from zmq.eventloop import ioloop

# Local imports.
from IPython.utils.traitlets import HasTraits, Any, Bool, Int, Instance, Str, \
    Type
from kernel import launch_kernel
from session import Session

# Constants.
LOCALHOST = '127.0.0.1'


class MissingHandlerError(Exception):
    pass


class ZmqSocketChannel(Thread):
    """ The base class for the channels that use ZMQ sockets.
    """

    def __init__(self, context, session, address=None):
        super(ZmqSocketChannel, self).__init__()
        self.daemon = True

        self.context = context
        self.session = session
        self.address = address
        self.socket = None

    def stop(self):
        """ Stop the thread's activity. Returns when the thread terminates.
        """
        self.join()

        # Allow the thread to be started again.
        # FIXME: Although this works (and there's no reason why it shouldn't),
        #        it feels wrong. Is there a cleaner way to achieve this?
        Thread.__init__(self)

    def get_address(self):
        """ Get the channel's address. By the default, a channel is on 
            localhost with no port specified (a negative port number).
        """
        return self._address

    def set_adresss(self, address):
        """ Set the channel's address. Should be a tuple of form:
                (ip address [str], port [int]).
            or None, in which case the address is reset to its default value.
        """
        # FIXME: Validate address.
        if self.is_alive():
            raise RuntimeError("Cannot set address on a running channel!")
        else:
            if address is None:
                address = (LOCALHOST, -1)
            self._address = address

    address = property(get_address, set_adresss)


class SubSocketChannel(ZmqSocketChannel):

    handlers = None
    _overriden_call_handler = None

    def __init__(self, context, session, address=None):
        self.handlers = {}
        super(SubSocketChannel, self).__init__(context, session, address)

    def run(self):
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE,'')
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.address)
        self.ioloop = ioloop.IOLoop()
        self.ioloop.add_handler(self.socket, self._handle_events, 
                                POLLIN|POLLERR)
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()
        super(SubSocketChannel, self).stop()

    def _handle_events(self, socket, events):
        # Turn on and off POLLOUT depending on if we have made a request
        if events & POLLERR:
            self._handle_err()
        if events & POLLIN:
            self._handle_recv()

    def _handle_err(self):
        raise zmq.ZmqError()

    def _handle_recv(self):
        msg = self.socket.recv_json()
        self.call_handlers(msg)

    def override_call_handler(self, func):
        """Permanently override the call_handler.
    
        The function func will be called as::

            func(handler, msg)

        And must call::
        
            handler(msg)

        in the main thread.
        """
        assert callable(func), "not a callable: %r" % func
        self._overriden_call_handler = func

    def call_handlers(self, msg):
        handler = self.handlers.get(msg['msg_type'], None)
        if handler is not None:
            try:
                self.call_handler(handler, msg)
            except:
                # XXX: This should be logged at least
                traceback.print_last()

    def call_handler(self, handler, msg):
        if self._overriden_call_handler is not None:
            self._overriden_call_handler(handler, msg)
        elif hasattr(self, '_call_handler'):
           call_handler = getattr(self, '_call_handler')
           call_handler(handler, msg)
        else:
            raise RuntimeError('no handler!')

    def add_handler(self, callback, msg_type):
        """Register a callback for msg type."""
        self.handlers[msg_type] = callback

    def remove_handler(self, msg_type):
        """Remove the callback for msg type."""
        self.handlers.pop(msg_type, None)

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
        
    def _flush(self):
        """Called in this thread by the IOLoop to indicate that all events have
        been processed.
        """
        self._flushed = True


class XReqSocketChannel(ZmqSocketChannel):

    handler_queue = None
    command_queue = None
    handlers = None
    _overriden_call_handler = None

    def __init__(self, context, session, address=None):
        self.handlers = {}
        self.handler_queue = Queue()
        self.command_queue = Queue()
        super(XReqSocketChannel, self).__init__(context, session, address)

    def run(self):
        self.socket = self.context.socket(zmq.XREQ)
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.address)
        self.ioloop = ioloop.IOLoop()
        self.ioloop.add_handler(self.socket, self._handle_events, 
                                POLLIN|POLLOUT|POLLERR)
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()
        super(XReqSocketChannel, self).stop()

    def _handle_events(self, socket, events):
        # Turn on and off POLLOUT depending on if we have made a request
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

    def _handle_err(self):
        raise zmq.ZmqError()

    def _queue_request(self, msg, callback):
        handler = self._find_handler(msg['msg_type'], callback)
        self.handler_queue.put(handler)
        self.command_queue.put(msg)

    def execute(self, code, callback=None):
        # Create class for content/msg creation. Related to, but possibly
        # not in Session.
        content = dict(code=code)
        msg = self.session.msg('execute_request', content)
        self._queue_request(msg, callback)
        return msg['header']['msg_id']

    def complete(self, text, line, block=None, callback=None):
        content = dict(text=text, line=line)
        msg = self.session.msg('complete_request', content)
        self._queue_request(msg, callback)
        return msg['header']['msg_id']

    def object_info(self, oname, callback=None):
        content = dict(oname=oname)
        msg = self.session.msg('object_info_request', content)
        self._queue_request(msg, callback)
        return msg['header']['msg_id']

    def _find_handler(self, name, callback):
        if callback is not None:
            return callback
        handler = self.handlers.get(name)
        if handler is None:
            raise MissingHandlerError(
                'No handler defined for method: %s' % name)
        return handler

    def override_call_handler(self, func):
        """Permanently override the call_handler.
    
        The function func will be called as::

            func(handler, msg)

        And must call::
        
            handler(msg)

        in the main thread.
        """
        assert callable(func), "not a callable: %r" % func
        self._overriden_call_handler = func

    def call_handlers(self, msg):
        try:
            handler = self.handler_queue.get(False)
        except Empty:
            print "Message received with no handler!!!"
            print msg
        else:
            self.call_handler(handler, msg)

    def call_handler(self, handler, msg):
        if self._overriden_call_handler is not None:
            self._overriden_call_handler(handler, msg)
        elif hasattr(self, '_call_handler'):
           call_handler = getattr(self, '_call_handler')
           call_handler(handler, msg)
        else:
            raise RuntimeError('no handler!')


class RepSocketChannel(ZmqSocketChannel):

    def on_raw_input(self):
        pass


class KernelManager(HasTraits):
    """ Manages a kernel for a frontend.

    The SUB channel is for the frontend to receive messages published by the
    kernel.
        
    The REQ channel is for the frontend to make requests of the kernel.
    
    The REP channel is for the kernel to request stdin (raw_input) from the
    frontend.
    """

    # Whether the kernel manager is currently listening on its channels.
    is_listening = Bool(False)

    # The PyZMQ Context to use for communication with the kernel.
    context = Instance(zmq.Context, ())

    # The Session to use for communication with the kernel.
    session = Instance(Session, ())

    # The classes to use for the various channels.
    sub_channel_class = Type(SubSocketChannel)
    xreq_channel_class = Type(XReqSocketChannel)
    rep_channel_class = Type(RepSocketChannel)
    
    # Protected traits.
    _kernel = Instance(Popen)
    _sub_channel = Any
    _xreq_channel = Any
    _rep_channel = Any

    #--------------------------------------------------------------------------
    # Channel management methods:
    #--------------------------------------------------------------------------

    def start_listening(self):
        """Starts listening on the specified ports. If already listening, raises
        a RuntimeError.
        """
        if self.is_listening:
            raise RuntimeError("Cannot start listening. Already listening!")
        else:
            self.is_listening = True
            self.sub_channel.start()
            self.xreq_channel.start()
            self.rep_channel.start()

    @property
    def is_alive(self):
        """ Returns whether the kernel is alive. """
        if self.is_listening:
            # TODO: check if alive.
            return True
        else:
            return False

    def stop_listening(self):
        """Stops listening. If not listening, does nothing. """
        if self.is_listening:
            self.is_listening = False
            self.sub_channel.stop()
            self.xreq_channel.stop()
            self.rep_channel.stop()

    #--------------------------------------------------------------------------
    # Kernel process management methods:
    #--------------------------------------------------------------------------

    def start_kernel(self):
        """Starts a kernel process and configures the manager to use it.

        If ports have been specified via the address attributes, they are used.
        Otherwise, open ports are chosen by the OS and the channel port
        attributes are configured as appropriate.
        """
        xreq, sub = self.xreq_address, self.sub_address
        if xreq[0] != LOCALHOST or sub[0] != LOCALHOST:
            raise RuntimeError("Can only launch a kernel on localhost."
                               "Make sure that the '*_address' attributes are "
                               "configured properly.")

        kernel, xrep, pub = launch_kernel(xrep_port=xreq[1], pub_port=sub[1])
        self.set_kernel(kernel)
        self.xreq_address = (LOCALHOST, xrep)
        self.sub_address = (LOCALHOST, pub)

    def set_kernel(self, kernel):
        """Sets the kernel manager's kernel to an existing kernel process.

        It is *not* necessary to a set a kernel to communicate with it via the
        channels, and those objects must be configured separately. It
        *is* necessary to set a kernel if you want to use the manager (or
        frontends that use the manager) to signal and/or kill the kernel.

        Parameters:
        -----------
        kernel : Popen
            An existing kernel process.
        """
        self._kernel = kernel

    @property
    def has_kernel(self):
        """Returns whether a kernel process has been specified for the kernel
        manager.

        A kernel process can be set via 'start_kernel' or 'set_kernel'.
        """
        return self._kernel is not None

    def kill_kernel(self):
        """ Kill the running kernel. """
        if self._kernel:
            self._kernel.kill()
            self._kernel = None
        else:
            raise RuntimeError("Cannot kill kernel. No kernel is running!")

    def signal_kernel(self, signum):
        """ Sends a signal to the kernel. """
        if self._kernel:
            self._kernel.send_signal(signum)
        else:
            raise RuntimeError("Cannot signal kernel. No kernel is running!")

    #--------------------------------------------------------------------------
    # Channels used for communication with the kernel:
    #--------------------------------------------------------------------------

    @property
    def sub_channel(self):
        """Get the SUB socket channel object."""
        if self._sub_channel is None:
            self._sub_channel = self.sub_channel_class(self.context,
                                                       self.session)
        return self._sub_channel

    @property
    def xreq_channel(self):
        """Get the REQ socket channel object to make requests of the kernel."""
        if self._xreq_channel is None:
            self._xreq_channel = self.xreq_channel_class(self.context, 
                                                         self.session)
        return self._xreq_channel

    @property
    def rep_channel(self):
        """Get the REP socket channel object to handle stdin (raw_input)."""
        if self._rep_channel is None:
            self._rep_channel = self.rep_channel_class(self.context, 
                                                       self.session)
        return self._rep_channel

    #--------------------------------------------------------------------------
    # Delegates for the Channel address attributes:
    #--------------------------------------------------------------------------

    def get_sub_address(self):
        return self.sub_channel.address

    def set_sub_address(self, address):
        self.sub_channel.address = address

    sub_address = property(get_sub_address, set_sub_address,
                           doc="The address used by SUB socket channel.")

    def get_xreq_address(self):
        return self.xreq_channel.address

    def set_xreq_address(self, address):
        self.xreq_channel.address = address

    xreq_address = property(get_xreq_address, set_xreq_address,
                            doc="The address used by XREQ socket channel.")
    
    def get_rep_address(self):
        return self.rep_channel.address

    def set_rep_address(self, address):
        self.rep_channel.address = address

    rep_address = property(get_rep_address, set_rep_address,
                           doc="The address used by REP socket channel.")
    
