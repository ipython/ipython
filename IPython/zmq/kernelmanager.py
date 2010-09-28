"""Base classes to manage the interaction with a running kernel.

TODO
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
import atexit
from Queue import Queue, Empty
from subprocess import Popen
import signal
import sys
from threading import Thread
import time

# System library imports.
import zmq
from zmq import POLLIN, POLLOUT, POLLERR
from zmq.eventloop import ioloop

# Local imports.
from IPython.utils import io
from IPython.utils.traitlets import HasTraits, Any, Instance, Type, TCPAddress
from session import Session

#-----------------------------------------------------------------------------
# Constants and exceptions
#-----------------------------------------------------------------------------

LOCALHOST = '127.0.0.1'

class InvalidPortNumber(Exception):
    pass

#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------

# some utilities to validate message structure, these might get moved elsewhere
# if they prove to have more generic utility

def validate_string_list(lst):
    """Validate that the input is a list of strings.

    Raises ValueError if not."""
    if not isinstance(lst, list):
        raise ValueError('input %r must be a list' % lst)
    for x in lst:
        if not isinstance(x, basestring):
            raise ValueError('element %r in list must be a string' % x)


def validate_string_dict(dct):
    """Validate that the input is a dict with string keys and values.

    Raises ValueError if not."""
    for k,v in dct.iteritems():
        if not isinstance(k, basestring):
            raise ValueError('key %r in dict must be a string' % k)
        if not isinstance(v, basestring):
            raise ValueError('value %r in dict must be a string' % v)


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
        context : :class:`zmq.Context`
            The ZMQ context to use.
        session : :class:`session.Session`
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
        super(XReqSocketChannel, self).__init__(context, session, address)
        self.command_queue = Queue()
        self.ioloop = ioloop.IOLoop()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.socket = self.context.socket(zmq.XREQ)
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.address)
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

    def execute(self, code, silent=False,
                user_variables=None, user_expressions=None):
        """Execute code in the kernel.

        Parameters
        ----------
        code : str
            A string of Python code.
            
        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible.

        user_variables : list, optional
            A list of variable names to pull from the user's namespace.  They
            will come back as a dict with these names as keys and their
            :func:`repr` as values.
            
        user_expressions : dict, optional
            A dict with string keys and  to pull from the user's
            namespace.  They will come back as a dict with these names as keys
            and their :func:`repr` as values.

        Returns
        -------
        The msg_id of the message sent.
        """
        if user_variables is None:
            user_variables = []
        if user_expressions is None:
            user_expressions = {}
            
        # Don't waste network traffic if inputs are invalid
        if not isinstance(code, basestring):
            raise ValueError('code %r must be a string' % code)
        validate_string_list(user_variables)
        validate_string_dict(user_expressions)

        # Create class for content/msg creation. Related to, but possibly
        # not in Session.
        content = dict(code=code, silent=silent,
                       user_variables=user_variables,
                       user_expressions=user_expressions)
        msg = self.session.msg('execute_request', content)
        self._queue_request(msg)
        return msg['header']['msg_id']

    def complete(self, text, line, cursor_pos, block=None):
        """Tab complete text in the kernel's namespace.

        Parameters
        ----------
        text : str
            The text to complete.
        line : str
            The full line of text that is the surrounding context for the 
            text to complete.
        cursor_pos : int
            The position of the cursor in the line where the completion was
            requested.
        block : str, optional
            The full block of code in which the completion is being requested.

        Returns
        -------
        The msg_id of the message sent.
        """
        content = dict(text=text, line=line, block=block, cursor_pos=cursor_pos)
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

    def history(self, index=None, raw=False, output=True):
        """Get the history list.

        Parameters
        ----------
        index : n or (n1, n2) or None
            If n, then the last entries. If a tuple, then all in
            range(n1, n2). If None, then all entries. Raises IndexError if
            the format of index is incorrect.
        raw : bool
            If True, return the raw input.
        output : bool
            If True, then return the output as well.

        Returns
        -------
        The msg_id of the message sent.
        """
        content = dict(index=index, raw=raw, output=output)
        msg = self.session.msg('history_request', content)
        self._queue_request(msg)
        return msg['header']['msg_id']

    def shutdown(self):
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
        msg = self.session.msg('shutdown_request', {})
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
        self.ioloop = ioloop.IOLoop()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE,'')
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.address)
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

        Callers should use this method to ensure that :method:`call_handlers`
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
                # Will this trigger POLLERR?
                break
            else:
                self.call_handlers(msg)

    def _flush(self):
        """Callback for :method:`self.flush`."""
        self._flushed = True


class RepSocketChannel(ZmqSocketChannel):
    """A reply channel to handle raw_input requests that the kernel makes."""

    msg_queue = None

    def __init__(self, context, session, address):
        super(RepSocketChannel, self).__init__(context, session, address)
        self.ioloop = ioloop.IOLoop()
        self.msg_queue = Queue()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.socket = self.context.socket(zmq.XREQ)
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.address)
        self.iostate = POLLERR|POLLIN
        self.ioloop.add_handler(self.socket, self._handle_events, 
                                self.iostate)
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()
        super(RepSocketChannel, self).stop()

    def call_handlers(self, msg):
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application leve
        handlers are called in the application thread.
        """
        raise NotImplementedError('call_handlers must be defined in a subclass.')

    def input(self, string):
        """Send a string of raw input to the kernel."""
        content = dict(value=string)
        msg = self.session.msg('input_reply', content)
        self._queue_reply(msg)

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
            msg = self.msg_queue.get(False)
        except Empty:
            pass
        else:
            self.socket.send_json(msg)
        if self.msg_queue.empty():
            self.drop_io_state(POLLOUT)

    def _handle_err(self):
        # We don't want to let this go silently, so eventually we should log.
        raise zmq.ZMQError()

    def _queue_reply(self, msg):
        self.msg_queue.put(msg)
        self.add_io_state(POLLOUT)


class HBSocketChannel(ZmqSocketChannel):
    """The heartbeat channel which monitors the kernel heartbeat.

    Note that the heartbeat channel is paused by default. As long as you start
    this channel, the kernel manager will ensure that it is paused and un-paused
    as appropriate.
    """

    time_to_dead = 3.0
    socket = None
    poller = None
    _running = None
    _pause = None

    def __init__(self, context, session, address):
        super(HBSocketChannel, self).__init__(context, session, address)
        self._running = False
        self._pause = True

    def _create_socket(self):
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.IDENTITY, self.session.session)
        self.socket.connect('tcp://%s:%i' % self.address)
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self._create_socket()
        self._running = True
        while self._running:
            if self._pause:
                time.sleep(self.time_to_dead)
            else:
                since_last_heartbeat = 0.0
                request_time = time.time()
                try:
                    #io.rprint('Ping from HB channel') # dbg
                    self.socket.send_json('ping')
                except zmq.ZMQError, e:
                    #io.rprint('*** HB Error:', e) # dbg
                    if e.errno == zmq.EFSM:
                        #io.rprint('sleep...', self.time_to_dead) # dbg
                        time.sleep(self.time_to_dead)
                        self._create_socket()
                    else:
                        raise
                else:
                    while True:
                        try:
                            self.socket.recv_json(zmq.NOBLOCK)
                        except zmq.ZMQError, e:
                            #io.rprint('*** HB Error 2:', e) # dbg
                            if e.errno == zmq.EAGAIN:
                                before_poll = time.time()
                                until_dead = self.time_to_dead - (before_poll -
                                                                  request_time)

                                # When the return value of poll() is an empty
                                # list, that is when things have gone wrong
                                # (zeromq bug). As long as it is not an empty
                                # list, poll is working correctly even if it
                                # returns quickly. Note: poll timeout is in
                                # milliseconds.
                                self.poller.poll(1000*until_dead)
                            
                                since_last_heartbeat = time.time()-request_time
                                if since_last_heartbeat > self.time_to_dead:
                                    self.call_handlers(since_last_heartbeat)
                                    break
                            else:
                                # FIXME: We should probably log this instead.
                                raise
                        else:
                            until_dead = self.time_to_dead - (time.time() -
                                                              request_time)
                            if until_dead > 0.0:
                                #io.rprint('sleep...', self.time_to_dead) # dbg
                                time.sleep(until_dead)
                            break

    def pause(self):
        """Pause the heartbeat."""
        self._pause = True

    def unpause(self):
        """Unpause the heartbeat."""
        self._pause = False

    def is_beating(self):
        """Is the heartbeat running and not paused."""
        if self.is_alive() and not self._pause:
            return True
        else:
            return False

    def stop(self):
        self._running = False
        super(HBSocketChannel, self).stop()

    def call_handlers(self, since_last_heartbeat):
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application leve
        handlers are called in the application thread.
        """
        raise NotImplementedError('call_handlers must be defined in a subclass.')


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
    context = Instance(zmq.Context,(),{})

    # The Session to use for communication with the kernel.
    session = Instance(Session,(),{})

    # The kernel process with which the KernelManager is communicating.
    kernel = Instance(Popen)

    # The addresses for the communication channels. 
    xreq_address = TCPAddress((LOCALHOST, 0))
    sub_address = TCPAddress((LOCALHOST, 0))
    rep_address = TCPAddress((LOCALHOST, 0))
    hb_address = TCPAddress((LOCALHOST, 0))

    # The classes to use for the various channels.
    xreq_channel_class = Type(XReqSocketChannel)
    sub_channel_class = Type(SubSocketChannel)
    rep_channel_class = Type(RepSocketChannel)
    hb_channel_class = Type(HBSocketChannel)

    # Protected traits.
    _launch_args = Any
    _xreq_channel = Any
    _sub_channel = Any
    _rep_channel = Any
    _hb_channel = Any

    def __init__(self, **kwargs):
        super(KernelManager, self).__init__(**kwargs)
        # Uncomment this to try closing the context.
        # atexit.register(self.context.close)

    #--------------------------------------------------------------------------
    # Channel management methods:
    #--------------------------------------------------------------------------

    def start_channels(self, xreq=True, sub=True, rep=True, hb=True):
        """Starts the channels for this kernel.

        This will create the channels if they do not exist and then start
        them. If port numbers of 0 are being used (random ports) then you
        must first call :method:`start_kernel`. If the channels have been
        stopped and you call this, :class:`RuntimeError` will be raised.
        """
        if xreq:
            self.xreq_channel.start()
        if sub:
            self.sub_channel.start()
        if rep:
            self.rep_channel.start()
        if hb:
            self.hb_channel.start()

    def stop_channels(self):
        """Stops all the running channels for this kernel.
        """
        if self.xreq_channel.is_alive():
            self.xreq_channel.stop()
        if self.sub_channel.is_alive():
            self.sub_channel.stop()
        if self.rep_channel.is_alive():
            self.rep_channel.stop()
        if self.hb_channel.is_alive():
            self.hb_channel.stop()

    @property
    def channels_running(self):
        """Are any of the channels created and running?"""
        return (self.xreq_channel.is_alive() or self.sub_channel.is_alive() or
                self.rep_channel.is_alive() or self.hb_channel.is_alive())

    #--------------------------------------------------------------------------
    # Kernel process management methods:
    #--------------------------------------------------------------------------

    def start_kernel(self, **kw):
        """Starts a kernel process and configures the manager to use it.

        If random ports (port=0) are being used, this method must be called
        before the channels are created.

        Parameters:
        -----------
        ipython : bool, optional (default True)
             Whether to use an IPython kernel instead of a plain Python kernel.
        """
        xreq, sub, rep, hb = self.xreq_address, self.sub_address, \
            self.rep_address, self.hb_address
        if xreq[0] != LOCALHOST or sub[0] != LOCALHOST or \
                rep[0] != LOCALHOST or hb[0] != LOCALHOST:
            raise RuntimeError("Can only launch a kernel on localhost."
                               "Make sure that the '*_address' attributes are "
                               "configured properly.")

        self._launch_args = kw.copy()
        if kw.pop('ipython', True):
            from ipkernel import launch_kernel
        else:
            from pykernel import launch_kernel
        self.kernel, xrep, pub, req, hb = launch_kernel(
            xrep_port=xreq[1], pub_port=sub[1], 
            req_port=rep[1], hb_port=hb[1], **kw)
        self.xreq_address = (LOCALHOST, xrep)
        self.sub_address = (LOCALHOST, pub)
        self.rep_address = (LOCALHOST, req)
        self.hb_address = (LOCALHOST, hb)

    def shutdown_kernel(self):
        """ Attempts to the stop the kernel process cleanly. If the kernel
        cannot be stopped, it is killed, if possible.
        """
        # FIXME: Shutdown does not work on Windows due to ZMQ errors!
        if sys.platform == 'win32':
            self.kill_kernel()
            return

        # Pause the heart beat channel if it exists.
        if self._hb_channel is not None:
            self._hb_channel.pause()

        # Don't send any additional kernel kill messages immediately, to give
        # the kernel a chance to properly execute shutdown actions. Wait for at
        # most 1s, checking every 0.1s.
        self.xreq_channel.shutdown()
        for i in range(10):
            if self.is_alive:
                time.sleep(0.1)
            else:
                break
        else:
            # OK, we've waited long enough.
            if self.has_kernel:
                self.kill_kernel()
    
    def restart_kernel(self, now=False):
        """Restarts a kernel with the same arguments that were used to launch
        it. If the old kernel was launched with random ports, the same ports
        will be used for the new kernel.

        Parameters
        ----------
        now : bool, optional
          If True, the kernel is forcefully restarted *immediately*, without
          having a chance to do any cleanup action.  Otherwise the kernel is
          given 1s to clean up before a forceful restart is issued.

          In all cases the kernel is restarted, the only difference is whether
          it is given a chance to perform a clean shutdown or not.
        """
        if self._launch_args is None:
            raise RuntimeError("Cannot restart the kernel. "
                               "No previous call to 'start_kernel'.")
        else:
            if self.has_kernel:
                if now:
                    self.kill_kernel()
                else:
                    self.shutdown_kernel()
            self.start_kernel(**self._launch_args)

            # FIXME: Messages get dropped in Windows due to probable ZMQ bug
            # unless there is some delay here.
            if sys.platform == 'win32':
                time.sleep(0.2)

    @property
    def has_kernel(self):
        """Returns whether a kernel process has been specified for the kernel
        manager.
        """
        return self.kernel is not None

    def kill_kernel(self):
        """ Kill the running kernel. """
        if self.has_kernel:
            # Pause the heart beat channel if it exists.
            if self._hb_channel is not None:
                self._hb_channel.pause()

            # Attempt to kill the kernel.
            try:
                self.kernel.kill()
            except OSError, e:
                # In Windows, we will get an Access Denied error if the process
                # has already terminated. Ignore it.
                if not (sys.platform == 'win32' and e.winerror == 5):
                    raise
            self.kernel = None
        else:
            raise RuntimeError("Cannot kill kernel. No kernel is running!")

    def interrupt_kernel(self):
        """ Interrupts the kernel. Unlike ``signal_kernel``, this operation is
        well supported on all platforms.
        """
        if self.has_kernel:
            if sys.platform == 'win32':
                from parentpoller import ParentPollerWindows as Poller
                Poller.send_interrupt(self.kernel.win32_interrupt_event)
            else:
                self.kernel.send_signal(signal.SIGINT)
        else:
            raise RuntimeError("Cannot interrupt kernel. No kernel is running!")

    def signal_kernel(self, signum):
        """ Sends a signal to the kernel. Note that since only SIGTERM is
        supported on Windows, this function is only useful on Unix systems.
        """
        if self.has_kernel:
            self.kernel.send_signal(signum)
        else:
            raise RuntimeError("Cannot signal kernel. No kernel is running!")

    @property
    def is_alive(self):
        """Is the kernel process still running?"""
        # FIXME: not using a heartbeat means this method is broken for any
        # remote kernel, it's only capable of handling local kernels.
        if self.has_kernel:
            if self.kernel.poll() is None:
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
    def hb_channel(self):
        """Get the REP socket channel object to handle stdin (raw_input)."""
        if self._hb_channel is None:
            self._hb_channel = self.hb_channel_class(self.context, 
                                                       self.session,
                                                       self.hb_address)
        return self._hb_channel
