"""Kernel frontend classes.

To do:

1. Create custom channel subclasses for Qt.
2. Create logger to handle debugging and console messages.

"""

from Queue import Queue, Empty
from threading import Thread
import traceback

import zmq
from zmq import POLLIN, POLLOUT, POLLERR
from zmq.eventloop import ioloop
from session import Session


class MissingHandlerError(Exception):
    pass


class KernelManager(object):

    def __init__(self, xreq_addr, sub_addr, rep_addr, 
                 context=None, session=None):
        self.context = zmq.Context() if context is None else context
        self.session = Session() if session is None else session
        self.xreq_addr = xreq_addr
        self.sub_addr = sub_addr
        self.rep_addr = rep_addr

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

    def get_sub_channel(self):
        """Get the SUB socket channel object."""
        return SubSocketChannel(self.context, self.session, self.sub_addr)
    
    def get_xreq_channel(self):
        """Get the REQ socket channel object to make requests of the kernel."""
        return XReqSocketChannel(self.context, self.session, self.xreq_addr)
    
    def get_rep_channel(self):
        """Get the REP socket channel object to handle stdin (raw_input)."""
        return RepSocketChannel(self.context, self.session, self.rep_addr)


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
        self.handlers.pop(msg_type, None)


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
        print "Got reply:", msg
        try:
            handler = self.handler_queue.get(False)
        except Empty:
            print "Message received with no handler!!!"
            print msg
        else:
            self.call_handler(handler, msg)

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
        return self._queue_request(msg, callback)
        return msg['header']['msg_id']

    def object_info(self, oname, callback=None):
        content = dict(oname=oname)
        msg = self.session.msg('object_info_request', content)
        return self._queue_request(msg, callback)
        return msg['header']['msg_id']

    def _find_handler(self, name, callback):
        if callback is not None:
            return callback
        handler = self.handlers.get(name)
        if handler is None:
            raise MissingHandlerError('No handler defined for method: %s' % name)
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
