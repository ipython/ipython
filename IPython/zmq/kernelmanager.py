"""Kernel frontend classes.

TODO: Create logger to handle debugging and console messages.

"""

# Standard library imports.
from Queue import Queue, Empty
from threading import Thread
import time
import traceback

# System library imports.
import zmq
from zmq import POLLIN, POLLOUT, POLLERR
from zmq.eventloop import ioloop

# Local imports.
from IPython.utils.traitlets import HasTraits, Any, Int, Instance, Str, Type
from session import Session


class MissingHandlerError(Exception):
    pass


class ZmqSocketChannel(Thread):

    socket = None

    def __init__(self, context, session, addr):
        self.context = context
        self.session = session
        self.addr = addr
        super(ZmqSocketChannel, self).__init__()
        self.daemon = True


class SubSocketChannel(ZmqSocketChannel):

    handlers = None
    _overriden_call_handler = None

    def __init__(self, context, session, addr):
        self.handlers = {}
        super(SubSocketChannel, self).__init__(context, session, addr)

    def run(self):
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE,'')
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.addr)
        self.ioloop = ioloop.IOLoop()
        self.ioloop.add_handler(self.socket, self._handle_events, 
                                POLLIN|POLLERR)
        self.ioloop.start()

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

    def flush(self):
        """Immediately processes all pending messages on the SUB channel. This
           method is thread safe.
        """
        self._flushed = False
        self.ioloop.add_callback(self._flush)
        while not self._flushed:
            time.sleep(0)
        
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

    def __init__(self, context, session, addr):
        self.handlers = {}
        self.handler_queue = Queue()
        self.command_queue = Queue()
        super(XReqSocketChannel, self).__init__(context, session, addr)

    def run(self):
        self.socket = self.context.socket(zmq.XREQ)
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.addr)
        self.ioloop = ioloop.IOLoop()
        self.ioloop.add_handler(self.socket, self._handle_events, 
                                POLLIN|POLLOUT|POLLERR)
        self.ioloop.start()

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

    def on_raw_input():
        pass


class KernelManager(HasTraits):

    # The addresses to use for the various channels. Should be tuples of form
    # (ip_address, port).
    sub_address = Any
    xreq_address = Any
    rep_address = Any
    # FIXME: Add Tuple to Traitlets.
    #sub_address = Tuple(Str, Int)
    #xreq_address = Tuple(Str, Int)
    #rep_address = Tuple(Str, Int)

    # The PyZMQ Context to use for communication with the kernel.
    context = Instance(zmq.Context, ())

    # The Session to use for communication with the kernel.
    session = Instance(Session, ())

    # The classes to use for the various channels.
    sub_channel_class = Type(SubSocketChannel)
    xreq_channel_class = Type(XReqSocketChannel)
    rep_channel_class = Type(RepSocketChannel)

    # Protected traits.
    _sub_channel = Any
    _xreq_channel = Any
    _rep_channel = Any

    def __init__(self, xreq_address, sub_address, rep_address, **traits):
        super(KernelManager, self).__init__()

        self.xreq_address = xreq_address
        self.sub_address = sub_address
        self.rep_address = rep_address

        # FIXME: This should be the business of HasTraits. The convention is:
        #        HasTraits.__init__(self, **traits_to_be_initialized.)
        for trait in traits:
            setattr(self, trait, traits[trait])

    def start_kernel(self):
        """Start a localhost kernel on ip and port.
        
        The SUB channel is for the frontend to receive messages published by
        the kernel.
        
        The REQ channel is for the frontend to make requests of the kernel.
        
        The REP channel is for the kernel to request stdin (raw_input) from 
        the frontend.
        """

    def kill_kernel(self):
        """Kill the running kernel"""

    def is_alive(self):
        """Is the kernel alive?"""
        return True

    def signal_kernel(self, signum):
        """Send signum to the kernel."""

    @property
    def sub_channel(self):
        """Get the SUB socket channel object."""
        if self._sub_channel is None:
            self._sub_channel = self.sub_channel_class(
                self.context, self.session, self.sub_address)
        return self._sub_channel

    @property
    def xreq_channel(self):
        """Get the REQ socket channel object to make requests of the kernel."""
        if self._xreq_channel is None:
            self._xreq_channel = self.xreq_channel_class(
                self.context, self.session, self.xreq_address)
        return self._xreq_channel

    @property
    def rep_channel(self):
        """Get the REP socket channel object to handle stdin (raw_input)."""
        if self._rep_channel is None:
            self._rep_channel = self.rep_channel_class(
                self.context, self.session, self.rep_address)
        return self._rep_channel
