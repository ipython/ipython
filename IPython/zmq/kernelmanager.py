"""Base classes to manage the interaction with a running kernel.

TODO
* Create logger to handle debugging and console messages.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports.
import atexit
import errno
import json
from subprocess import Popen
import os
import signal
import sys
from threading import Thread
import time

# System library imports.
import zmq
# import ZMQError in top-level namespace, to avoid ugly attribute-error messages
# during garbage collection of threads at exit:
from zmq import ZMQError
from zmq.eventloop import ioloop, zmqstream

# Local imports.
from IPython.config.loader import Config
from IPython.utils.localinterfaces import LOCALHOST, LOCAL_IPS
from IPython.utils.traitlets import (
    HasTraits, Any, Instance, Type, Unicode, Integer, Bool, CaselessStrEnum
)
from IPython.utils.py3compat import str_to_bytes
from IPython.zmq.entry_point import write_connection_file
from session import Session

#-----------------------------------------------------------------------------
# Constants and exceptions
#-----------------------------------------------------------------------------

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

class ZMQSocketChannel(Thread):
    """The base class for the channels that use ZMQ sockets.
    """
    context = None
    session = None
    socket = None
    ioloop = None
    stream = None
    _address = None
    _exiting = False

    def __init__(self, context, session, address):
        """Create a channel

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

    def stop(self):
        """Stop the channel's activity.

        This calls :method:`Thread.join` and returns when the thread
        terminates. :class:`RuntimeError` will be raised if
        :method:`self.start` is called again.
        """
        self.join()

    @property
    def address(self):
        """Get the channel's address as a zmq url string ('tcp://127.0.0.1:5555').
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
        """callback for stream.on_recv
        
        unpacks message, and calls handlers with it.
        """
        ident,smsg = self.session.feed_identities(msg)
        self.call_handlers(self.session.unserialize(smsg))
    


class ShellSocketChannel(ZMQSocketChannel):
    """The DEALER channel for issues request/replies to the kernel.
    """

    command_queue = None
    # flag for whether execute requests should be allowed to call raw_input:
    allow_stdin = True

    def __init__(self, context, session, address):
        super(ShellSocketChannel, self).__init__(context, session, address)
        self.ioloop = ioloop.IOLoop()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.session.bsession)
        self.socket.connect(self.address)
        self.stream = zmqstream.ZMQStream(self.socket, self.ioloop)
        self.stream.on_recv(self._handle_recv)
        self._run_loop()
        try:
            self.socket.close()
        except:
            pass

    def stop(self):
        self.ioloop.stop()
        super(ShellSocketChannel, self).stop()

    def call_handlers(self, msg):
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application leve
        handlers are called in the application thread.
        """
        raise NotImplementedError('call_handlers must be defined in a subclass.')

    def execute(self, code, silent=False, store_history=True,
                user_variables=None, user_expressions=None, allow_stdin=None):
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

        user_variables : list, optional
            A list of variable names to pull from the user's namespace.  They
            will come back as a dict with these names as keys and their
            :func:`repr` as values.

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
        if user_variables is None:
            user_variables = []
        if user_expressions is None:
            user_expressions = {}
        if allow_stdin is None:
            allow_stdin = self.allow_stdin
        
        
        # Don't waste network traffic if inputs are invalid
        if not isinstance(code, basestring):
            raise ValueError('code %r must be a string' % code)
        validate_string_list(user_variables)
        validate_string_dict(user_expressions)

        # Create class for content/msg creation. Related to, but possibly
        # not in Session.
        content = dict(code=code, silent=silent, store_history=store_history,
                       user_variables=user_variables,
                       user_expressions=user_expressions,
                       allow_stdin=allow_stdin,
                       )
        msg = self.session.msg('execute_request', content)
        self._queue_send(msg)
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
        self._queue_send(msg)
        return msg['header']['msg_id']

    def object_info(self, oname, detail_level=0):
        """Get metadata information about an object.

        Parameters
        ----------
        oname : str
            A string specifying the object name.
        detail_level : int, optional
            The level of detail for the introspection (0-2)

        Returns
        -------
        The msg_id of the message sent.
        """
        content = dict(oname=oname, detail_level=detail_level)
        msg = self.session.msg('object_info_request', content)
        self._queue_send(msg)
        return msg['header']['msg_id']

    def history(self, raw=True, output=False, hist_access_type='range', **kwargs):
        """Get entries from the history list.

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



class SubSocketChannel(ZMQSocketChannel):
    """The SUB channel which listens for messages that the kernel publishes.
    """

    def __init__(self, context, session, address):
        super(SubSocketChannel, self).__init__(context, session, address)
        self.ioloop = ioloop.IOLoop()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE,b'')
        self.socket.setsockopt(zmq.IDENTITY, self.session.bsession)
        self.socket.connect(self.address)
        self.stream = zmqstream.ZMQStream(self.socket, self.ioloop)
        self.stream.on_recv(self._handle_recv)
        self._run_loop()
        try:
            self.socket.close()
        except:
            pass

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

    def _flush(self):
        """Callback for :method:`self.flush`."""
        self.stream.flush()
        self._flushed = True


class StdInSocketChannel(ZMQSocketChannel):
    """A reply channel to handle raw_input requests that the kernel makes."""

    msg_queue = None

    def __init__(self, context, session, address):
        super(StdInSocketChannel, self).__init__(context, session, address)
        self.ioloop = ioloop.IOLoop()

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.session.bsession)
        self.socket.connect(self.address)
        self.stream = zmqstream.ZMQStream(self.socket, self.ioloop)
        self.stream.on_recv(self._handle_recv)
        self._run_loop()
        try:
            self.socket.close()
        except:
            pass
        

    def stop(self):
        self.ioloop.stop()
        super(StdInSocketChannel, self).stop()

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
        self._queue_send(msg)


class HBSocketChannel(ZMQSocketChannel):
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
    _beating = None

    def __init__(self, context, session, address):
        super(HBSocketChannel, self).__init__(context, session, address)
        self._running = False
        self._pause =True
        self.poller = zmq.Poller()

    def _create_socket(self):
        if self.socket is not None:
            # close previous socket, before opening a new one
            self.poller.unregister(self.socket)
            self.socket.close()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(self.address)
        
        self.poller.register(self.socket, zmq.POLLIN)
    
    def _poll(self, start_time):
        """poll for heartbeat replies until we reach self.time_to_dead
        
        Ignores interrupts, and returns the result of poll(), which
        will be an empty list if no messages arrived before the timeout,
        or the event tuple if there is a message to receive.
        """
        
        until_dead = self.time_to_dead - (time.time() - start_time)
        # ensure poll at least once
        until_dead = max(until_dead, 1e-3)
        events = []
        while True:
            try:
                events = self.poller.poll(1000 * until_dead)
            except ZMQError as e:
                if e.errno == errno.EINTR:
                    # ignore interrupts during heartbeat
                    # this may never actually happen
                    until_dead = self.time_to_dead - (time.time() - start_time)
                    until_dead = max(until_dead, 1e-3)
                    pass
                else:
                    raise
            except Exception:
                if self._exiting:
                    break
                else:
                    raise
            else:
                break
        return events

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self._create_socket()
        self._running = True
        self._beating = True
        
        while self._running:
            if self._pause:
                # just sleep, and skip the rest of the loop
                time.sleep(self.time_to_dead)
                continue
            
            since_last_heartbeat = 0.0
            # io.rprint('Ping from HB channel') # dbg
            # no need to catch EFSM here, because the previous event was
            # either a recv or connect, which cannot be followed by EFSM
            self.socket.send(b'ping')
            request_time = time.time()
            ready = self._poll(request_time)
            if ready:
                self._beating = True
                # the poll above guarantees we have something to recv
                self.socket.recv()
                # sleep the remainder of the cycle
                remainder = self.time_to_dead - (time.time() - request_time)
                if remainder > 0:
                    time.sleep(remainder)
                continue
            else:
                # nothing was received within the time limit, signal heart failure
                self._beating = False
                since_last_heartbeat = time.time() - request_time
                self.call_handlers(since_last_heartbeat)
                # and close/reopen the socket, because the REQ/REP cycle has been broken
                self._create_socket()
                continue
        try:
            self.socket.close()
        except:
            pass

    def pause(self):
        """Pause the heartbeat."""
        self._pause = True

    def unpause(self):
        """Unpause the heartbeat."""
        self._pause = False

    def is_beating(self):
        """Is the heartbeat running and responsive (and not paused)."""
        if self.is_alive() and not self._pause and self._beating:
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
        so that some logic must be done to ensure that the application level
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
    # config object for passing to child configurables
    config = Instance(Config)

    # The PyZMQ Context to use for communication with the kernel.
    context = Instance(zmq.Context)
    def _context_default(self):
        return zmq.Context.instance()

    # The Session to use for communication with the kernel.
    session = Instance(Session)

    # The kernel process with which the KernelManager is communicating.
    kernel = Instance(Popen)

    # The addresses for the communication channels.
    connection_file = Unicode('')
    
    transport = CaselessStrEnum(['tcp', 'ipc'], default_value='tcp')
    
    
    ip = Unicode(LOCALHOST)
    def _ip_changed(self, name, old, new):
        if new == '*':
            self.ip = '0.0.0.0'
    shell_port = Integer(0)
    iopub_port = Integer(0)
    stdin_port = Integer(0)
    hb_port = Integer(0)

    # The classes to use for the various channels.
    shell_channel_class = Type(ShellSocketChannel)
    sub_channel_class = Type(SubSocketChannel)
    stdin_channel_class = Type(StdInSocketChannel)
    hb_channel_class = Type(HBSocketChannel)

    # Protected traits.
    _launch_args = Any
    _shell_channel = Any
    _sub_channel = Any
    _stdin_channel = Any
    _hb_channel = Any
    _connection_file_written=Bool(False)

    def __init__(self, **kwargs):
        super(KernelManager, self).__init__(**kwargs)
        if self.session is None:
            self.session = Session(config=self.config)
    
    def __del__(self):
        self.cleanup_connection_file()
    

    #--------------------------------------------------------------------------
    # Channel management methods:
    #--------------------------------------------------------------------------

    def start_channels(self, shell=True, sub=True, stdin=True, hb=True):
        """Starts the channels for this kernel.

        This will create the channels if they do not exist and then start
        them. If port numbers of 0 are being used (random ports) then you
        must first call :method:`start_kernel`. If the channels have been
        stopped and you call this, :class:`RuntimeError` will be raised.
        """
        if shell:
            self.shell_channel.start()
        if sub:
            self.sub_channel.start()
        if stdin:
            self.stdin_channel.start()
            self.shell_channel.allow_stdin = True
        else:
            self.shell_channel.allow_stdin = False
        if hb:
            self.hb_channel.start()

    def stop_channels(self):
        """Stops all the running channels for this kernel.
        """
        if self.shell_channel.is_alive():
            self.shell_channel.stop()
        if self.sub_channel.is_alive():
            self.sub_channel.stop()
        if self.stdin_channel.is_alive():
            self.stdin_channel.stop()
        if self.hb_channel.is_alive():
            self.hb_channel.stop()

    @property
    def channels_running(self):
        """Are any of the channels created and running?"""
        return (self.shell_channel.is_alive() or self.sub_channel.is_alive() or
                self.stdin_channel.is_alive() or self.hb_channel.is_alive())

    #--------------------------------------------------------------------------
    # Kernel process management methods:
    #--------------------------------------------------------------------------
    
    def cleanup_connection_file(self):
        """cleanup connection file *if we wrote it*
        
        Will not raise if the connection file was already removed somehow.
        """
        if self._connection_file_written:
            # cleanup connection files on full shutdown of kernel we started
            self._connection_file_written = False
            try:
                os.remove(self.connection_file)
            except (IOError, OSError):
                pass
            
            self._cleanup_ipc_files()
    
    def _cleanup_ipc_files(self):
        """cleanup ipc files if we wrote them"""
        if self.transport != 'ipc':
            return
        for port in (self.shell_port, self.iopub_port, self.stdin_port, self.hb_port):
            ipcfile = "%s-%i" % (self.ip, port)
            try:
                os.remove(ipcfile)
            except (IOError, OSError):
                pass
    
    def load_connection_file(self):
        """load connection info from JSON dict in self.connection_file"""
        with open(self.connection_file) as f:
            cfg = json.loads(f.read())
        
        from pprint import pprint
        pprint(cfg)
        self.transport = cfg.get('transport', 'tcp')
        self.ip = cfg['ip']
        self.shell_port = cfg['shell_port']
        self.stdin_port = cfg['stdin_port']
        self.iopub_port = cfg['iopub_port']
        self.hb_port = cfg['hb_port']
        self.session.key = str_to_bytes(cfg['key'])
    
    def write_connection_file(self):
        """write connection info to JSON dict in self.connection_file"""
        if self._connection_file_written:
            return
        self.connection_file,cfg = write_connection_file(self.connection_file,
            transport=self.transport, ip=self.ip, key=self.session.key,
            stdin_port=self.stdin_port, iopub_port=self.iopub_port,
            shell_port=self.shell_port, hb_port=self.hb_port)
        # write_connection_file also sets default ports:
        self.shell_port = cfg['shell_port']
        self.stdin_port = cfg['stdin_port']
        self.iopub_port = cfg['iopub_port']
        self.hb_port = cfg['hb_port']
        
        self._connection_file_written = True
    
    def start_kernel(self, **kw):
        """Starts a kernel process and configures the manager to use it.

        If random ports (port=0) are being used, this method must be called
        before the channels are created.

        Parameters:
        -----------
        launcher : callable, optional (default None)
             A custom function for launching the kernel process (generally a
             wrapper around ``entry_point.base_launch_kernel``). In most cases,
             it should not be necessary to use this parameter.

        **kw : optional
             See respective options for IPython and Python kernels.
        """
        if self.transport == 'tcp' and self.ip not in LOCAL_IPS:
            raise RuntimeError("Can only launch a kernel on a local interface. "
                               "Make sure that the '*_address' attributes are "
                               "configured properly. "
                               "Currently valid addresses are: %s"%LOCAL_IPS
                               )
        
        # write connection file / get default ports
        self.write_connection_file()

        self._launch_args = kw.copy()
        launch_kernel = kw.pop('launcher', None)
        if launch_kernel is None:
            from ipkernel import launch_kernel
        self.kernel = launch_kernel(fname=self.connection_file, **kw)

    def shutdown_kernel(self, restart=False):
        """ Attempts to the stop the kernel process cleanly. 

        If the kernel cannot be stopped and the kernel is local, it is killed.
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
        self.shell_channel.shutdown(restart=restart)
        for i in range(10):
            if self.is_alive:
                time.sleep(0.1)
            else:
                break
        else:
            # OK, we've waited long enough.
            if self.has_kernel:
                self.kill_kernel()

        if not restart and self._connection_file_written:
            # cleanup connection files on full shutdown of kernel we started
            self._connection_file_written = False
            try:
                os.remove(self.connection_file)
            except IOError:
                pass

    def restart_kernel(self, now=False, **kw):
        """Restarts a kernel with the arguments that were used to launch it.

        If the old kernel was launched with random ports, the same ports will be
        used for the new kernel.

        Parameters
        ----------
        now : bool, optional
            If True, the kernel is forcefully restarted *immediately*, without
            having a chance to do any cleanup action.  Otherwise the kernel is
            given 1s to clean up before a forceful restart is issued.

            In all cases the kernel is restarted, the only difference is whether
            it is given a chance to perform a clean shutdown or not.

        **kw : optional
            Any options specified here will replace those used to launch the
            kernel.
        """
        if self._launch_args is None:
            raise RuntimeError("Cannot restart the kernel. "
                               "No previous call to 'start_kernel'.")
        else:
            # Stop currently running kernel.
            if self.has_kernel:
                if now:
                    self.kill_kernel()
                else:
                    self.shutdown_kernel(restart=True)

            # Start new kernel.
            self._launch_args.update(kw)
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
        """ Kill the running kernel.

        This method blocks until the kernel process has terminated.
        """
        if self.has_kernel:
            # Pause the heart beat channel if it exists.
            if self._hb_channel is not None:
                self._hb_channel.pause()

            # Signal the kernel to terminate (sends SIGKILL on Unix and calls
            # TerminateProcess() on Win32).
            try:
                self.kernel.kill()
            except OSError as e:
                # In Windows, we will get an Access Denied error if the process
                # has already terminated. Ignore it.
                if sys.platform == 'win32':
                    if e.winerror != 5:
                        raise
                # On Unix, we may get an ESRCH error if the process has already
                # terminated. Ignore it.
                else:
                    from errno import ESRCH
                    if e.errno != ESRCH:
                        raise

            # Block until the kernel terminates.
            self.kernel.wait()
            self.kernel = None
        else:
            raise RuntimeError("Cannot kill kernel. No kernel is running!")

    def interrupt_kernel(self):
        """ Interrupts the kernel.

        Unlike ``signal_kernel``, this operation is well supported on all
        platforms.
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
        """ Sends a signal to the kernel.

        Note that since only SIGTERM is supported on Windows, this function is
        only useful on Unix systems.
        """
        if self.has_kernel:
            self.kernel.send_signal(signum)
        else:
            raise RuntimeError("Cannot signal kernel. No kernel is running!")

    @property
    def is_alive(self):
        """Is the kernel process still running?"""
        if self.has_kernel:
            if self.kernel.poll() is None:
                return True
            else:
                return False
        elif self._hb_channel is not None:
            # We didn't start the kernel with this KernelManager so we
            # use the heartbeat.
            return self._hb_channel.is_beating()
        else:
            # no heartbeat and not local, we can't tell if it's running,
            # so naively return True
            return True

    #--------------------------------------------------------------------------
    # Channels used for communication with the kernel:
    #--------------------------------------------------------------------------

    def _make_url(self, port):
        """make a zmq url with a port"""
        if self.transport == 'tcp':
            return "tcp://%s:%i" % (self.ip, port)
        else:
            return "%s://%s-%s" % (self.transport, self.ip, port)

    @property
    def shell_channel(self):
        """Get the REQ socket channel object to make requests of the kernel."""
        if self._shell_channel is None:
            self._shell_channel = self.shell_channel_class(self.context,
                                                           self.session,
                                                           self._make_url(self.shell_port),
            )
        return self._shell_channel

    @property
    def sub_channel(self):
        """Get the SUB socket channel object."""
        if self._sub_channel is None:
            self._sub_channel = self.sub_channel_class(self.context,
                                                       self.session,
                                                       self._make_url(self.iopub_port),
            )
        return self._sub_channel

    @property
    def stdin_channel(self):
        """Get the REP socket channel object to handle stdin (raw_input)."""
        if self._stdin_channel is None:
            self._stdin_channel = self.stdin_channel_class(self.context,
                                                           self.session,
                                                           self._make_url(self.stdin_port),
            )
        return self._stdin_channel

    @property
    def hb_channel(self):
        """Get the heartbeat socket channel object to check that the
        kernel is alive."""
        if self._hb_channel is None:
            self._hb_channel = self.hb_channel_class(self.context,
                                                     self.session,
                                                     self._make_url(self.hb_port),
            )
        return self._hb_channel
