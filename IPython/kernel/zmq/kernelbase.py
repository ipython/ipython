"""Base class for a kernel that talks to frontends over 0MQ."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import sys
import time
import logging
import uuid

from datetime import datetime
from signal import (
        signal, default_int_handler, SIGINT
)

import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream

from IPython.config.configurable import SingletonConfigurable
from IPython.core.error import StdinNotImplementedError
from IPython.core import release
from IPython.utils import py3compat
from IPython.utils.py3compat import unicode_type, string_types
from IPython.utils.jsonutil import json_clean
from IPython.utils.traitlets import (
    Any, Instance, Float, Dict, List, Set, Integer, Unicode, Bool,
)

from .session import Session


class Kernel(SingletonConfigurable):

    #---------------------------------------------------------------------------
    # Kernel interface
    #---------------------------------------------------------------------------

    # attribute to override with a GUI
    eventloop = Any(None)
    def _eventloop_changed(self, name, old, new):
        """schedule call to eventloop from IOLoop"""
        loop = ioloop.IOLoop.instance()
        loop.add_callback(self.enter_eventloop)

    session = Instance(Session)
    profile_dir = Instance('IPython.core.profiledir.ProfileDir')
    shell_streams = List()
    control_stream = Instance(ZMQStream)
    iopub_socket = Instance(zmq.Socket)
    stdin_socket = Instance(zmq.Socket)
    log = Instance(logging.Logger)

    # identities:
    int_id = Integer(-1)
    ident = Unicode()

    def _ident_default(self):
        return unicode_type(uuid.uuid4())

    # This should be overridden by wrapper kernels that implement any real
    # language.
    language_info = {}
    
    # any links that should go in the help menu
    help_links = List()

    # Private interface
    
    _darwin_app_nap = Bool(True, config=True,
        help="""Whether to use appnope for compatiblity with OS X App Nap.
        
        Only affects OS X >= 10.9.
        """
    )

    # track associations with current request
    _allow_stdin = Bool(False)
    _parent_header = Dict()
    _parent_ident = Any(b'')
    # Time to sleep after flushing the stdout/err buffers in each execute
    # cycle.  While this introduces a hard limit on the minimal latency of the
    # execute cycle, it helps prevent output synchronization problems for
    # clients.
    # Units are in seconds.  The minimum zmq latency on local host is probably
    # ~150 microseconds, set this to 500us for now.  We may need to increase it
    # a little if it's not enough after more interactive testing.
    _execute_sleep = Float(0.0005, config=True)

    # Frequency of the kernel's event loop.
    # Units are in seconds, kernel subclasses for GUI toolkits may need to
    # adapt to milliseconds.
    _poll_interval = Float(0.05, config=True)

    # If the shutdown was requested over the network, we leave here the
    # necessary reply message so it can be sent by our registered atexit
    # handler.  This ensures that the reply is only sent to clients truly at
    # the end of our shutdown process (which happens after the underlying
    # IPython shell's own shutdown).
    _shutdown_message = None

    # This is a dict of port number that the kernel is listening on. It is set
    # by record_ports and used by connect_request.
    _recorded_ports = Dict()

    # set of aborted msg_ids
    aborted = Set()

    # Track execution count here. For IPython, we override this to use the
    # execution count we store in the shell.
    execution_count = 0


    def __init__(self, **kwargs):
        super(Kernel, self).__init__(**kwargs)

        # Build dict of handlers for message types
        msg_types = [ 'execute_request', 'complete_request',
                      'inspect_request', 'history_request',
                      'kernel_info_request',
                      'connect_request', 'shutdown_request',
                      'apply_request', 'is_complete_request',
                    ]
        self.shell_handlers = {}
        for msg_type in msg_types:
            self.shell_handlers[msg_type] = getattr(self, msg_type)
        
        control_msg_types = msg_types + [ 'clear_request', 'abort_request' ]
        self.control_handlers = {}
        for msg_type in control_msg_types:
            self.control_handlers[msg_type] = getattr(self, msg_type)

    
    def dispatch_control(self, msg):
        """dispatch control requests"""
        idents,msg = self.session.feed_identities(msg, copy=False)
        try:
            msg = self.session.deserialize(msg, content=True, copy=False)
        except:
            self.log.error("Invalid Control Message", exc_info=True)
            return

        self.log.debug("Control received: %s", msg)
        
        # Set the parent message for side effects.
        self.set_parent(idents, msg)
        self._publish_status(u'busy')
        
        header = msg['header']
        msg_type = header['msg_type']

        handler = self.control_handlers.get(msg_type, None)
        if handler is None:
            self.log.error("UNKNOWN CONTROL MESSAGE TYPE: %r", msg_type)
        else:
            try:
                handler(self.control_stream, idents, msg)
            except Exception:
                self.log.error("Exception in control handler:", exc_info=True)
        
        sys.stdout.flush()
        sys.stderr.flush()
        self._publish_status(u'idle')
    
    def dispatch_shell(self, stream, msg):
        """dispatch shell requests"""
        # flush control requests first
        if self.control_stream:
            self.control_stream.flush()
        
        idents,msg = self.session.feed_identities(msg, copy=False)
        try:
            msg = self.session.deserialize(msg, content=True, copy=False)
        except:
            self.log.error("Invalid Message", exc_info=True)
            return

        # Set the parent message for side effects.
        self.set_parent(idents, msg)
        self._publish_status(u'busy')
        
        header = msg['header']
        msg_id = header['msg_id']
        msg_type = msg['header']['msg_type']
        
        # Print some info about this message and leave a '--->' marker, so it's
        # easier to trace visually the message chain when debugging.  Each
        # handler prints its message at the end.
        self.log.debug('\n*** MESSAGE TYPE:%s***', msg_type)
        self.log.debug('   Content: %s\n   --->\n   ', msg['content'])

        if msg_id in self.aborted:
            self.aborted.remove(msg_id)
            # is it safe to assume a msg_id will not be resubmitted?
            reply_type = msg_type.split('_')[0] + '_reply'
            status = {'status' : 'aborted'}
            md = {'engine' : self.ident}
            md.update(status)
            self.session.send(stream, reply_type, metadata=md,
                        content=status, parent=msg, ident=idents)
            return
        
        handler = self.shell_handlers.get(msg_type, None)
        if handler is None:
            self.log.error("UNKNOWN MESSAGE TYPE: %r", msg_type)
        else:
            # ensure default_int_handler during handler call
            sig = signal(SIGINT, default_int_handler)
            self.log.debug("%s: %s", msg_type, msg)
            try:
                handler(stream, idents, msg)
            except Exception:
                self.log.error("Exception in message handler:", exc_info=True)
            finally:
                signal(SIGINT, sig)
        
        sys.stdout.flush()
        sys.stderr.flush()
        self._publish_status(u'idle')
    
    def enter_eventloop(self):
        """enter eventloop"""
        self.log.info("entering eventloop %s", self.eventloop)
        for stream in self.shell_streams:
            # flush any pending replies,
            # which may be skipped by entering the eventloop
            stream.flush(zmq.POLLOUT)
        # restore default_int_handler
        signal(SIGINT, default_int_handler)
        while self.eventloop is not None:
            try:
                self.eventloop(self)
            except KeyboardInterrupt:
                # Ctrl-C shouldn't crash the kernel
                self.log.error("KeyboardInterrupt caught in kernel")
                continue
            else:
                # eventloop exited cleanly, this means we should stop (right?)
                self.eventloop = None
                break
        self.log.info("exiting eventloop")

    def start(self):
        """register dispatchers for streams"""
        if self.control_stream:
            self.control_stream.on_recv(self.dispatch_control, copy=False)

        def make_dispatcher(stream):
            def dispatcher(msg):
                return self.dispatch_shell(stream, msg)
            return dispatcher

        for s in self.shell_streams:
            s.on_recv(make_dispatcher(s), copy=False)

        # publish idle status
        self._publish_status('starting')
    
    def do_one_iteration(self):
        """step eventloop just once"""
        if self.control_stream:
            self.control_stream.flush()
        for stream in self.shell_streams:
            # handle at most one request per iteration
            stream.flush(zmq.POLLIN, 1)
            stream.flush(zmq.POLLOUT)


    def record_ports(self, ports):
        """Record the ports that this kernel is using.

        The creator of the Kernel instance must call this methods if they
        want the :meth:`connect_request` method to return the port numbers.
        """
        self._recorded_ports = ports

    #---------------------------------------------------------------------------
    # Kernel request handlers
    #---------------------------------------------------------------------------
    
    def _make_metadata(self, other=None):
        """init metadata dict, for execute/apply_reply"""
        new_md = {
            'dependencies_met' : True,
            'engine' : self.ident,
            'started': datetime.now(),
        }
        if other:
            new_md.update(other)
        return new_md
    
    def _publish_execute_input(self, code, parent, execution_count):
        """Publish the code request on the iopub stream."""

        self.session.send(self.iopub_socket, u'execute_input',
                            {u'code':code, u'execution_count': execution_count},
                            parent=parent, ident=self._topic('execute_input')
        )
    
    def _publish_status(self, status, parent=None):
        """send status (busy/idle) on IOPub"""
        self.session.send(self.iopub_socket,
                          u'status',
                          {u'execution_state': status},
                          parent=parent or self._parent_header,
                          ident=self._topic('status'),
                          )
    
    def set_parent(self, ident, parent):
        """Set the current parent_header
        
        Side effects (IOPub messages) and replies are associated with
        the request that caused them via the parent_header.
        
        The parent identity is used to route input_request messages
        on the stdin channel.
        """
        self._parent_ident = ident
        self._parent_header = parent
    
    def send_response(self, stream, msg_or_type, content=None, ident=None,
             buffers=None, track=False, header=None, metadata=None):
        """Send a response to the message we're currently processing.
        
        This accepts all the parameters of :meth:`IPython.kernel.zmq.session.Session.send`
        except ``parent``.
        
        This relies on :meth:`set_parent` having been called for the current
        message.
        """
        return self.session.send(stream, msg_or_type, content, self._parent_header,
                                 ident, buffers, track, header, metadata)
    
    def execute_request(self, stream, ident, parent):
        """handle an execute_request"""
        
        try:
            content = parent[u'content']
            code = py3compat.cast_unicode_py2(content[u'code'])
            silent = content[u'silent']
            store_history = content.get(u'store_history', not silent)
            user_expressions = content.get('user_expressions', {})
            allow_stdin = content.get('allow_stdin', False)
        except:
            self.log.error("Got bad msg: ")
            self.log.error("%s", parent)
            return
        
        stop_on_error = content.get('stop_on_error', True)

        md = self._make_metadata(parent['metadata'])
        
        # Re-broadcast our input for the benefit of listening clients, and
        # start computing output
        if not silent:
            self.execution_count += 1
            self._publish_execute_input(code, parent, self.execution_count)
        
        reply_content = self.do_execute(code, silent, store_history,
                                        user_expressions, allow_stdin)

        # Flush output before sending the reply.
        sys.stdout.flush()
        sys.stderr.flush()
        # FIXME: on rare occasions, the flush doesn't seem to make it to the
        # clients... This seems to mitigate the problem, but we definitely need
        # to better understand what's going on.
        if self._execute_sleep:
            time.sleep(self._execute_sleep)

        # Send the reply.
        reply_content = json_clean(reply_content)
        
        md['status'] = reply_content['status']
        if reply_content['status'] == 'error' and \
                        reply_content['ename'] == 'UnmetDependency':
                md['dependencies_met'] = False

        reply_msg = self.session.send(stream, u'execute_reply',
                                      reply_content, parent, metadata=md,
                                      ident=ident)
        
        self.log.debug("%s", reply_msg)

        if not silent and reply_msg['content']['status'] == u'error' and stop_on_error:
            self._abort_queues()

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        """Execute user code. Must be overridden by subclasses.
        """
        raise NotImplementedError

    def complete_request(self, stream, ident, parent):
        content = parent['content']
        code = content['code']
        cursor_pos = content['cursor_pos']
        
        matches = self.do_complete(code, cursor_pos)
        matches = json_clean(matches)
        completion_msg = self.session.send(stream, 'complete_reply',
                                           matches, parent, ident)
        self.log.debug("%s", completion_msg)

    def do_complete(self, code, cursor_pos):
        """Override in subclasses to find completions.
        """
        return {'matches' : [],
                'cursor_end' : cursor_pos,
                'cursor_start' : cursor_pos,
                'metadata' : {},
                'status' : 'ok'}

    def inspect_request(self, stream, ident, parent):
        content = parent['content']
        
        reply_content = self.do_inspect(content['code'], content['cursor_pos'],
                                        content.get('detail_level', 0))
        # Before we send this object over, we scrub it for JSON usage
        reply_content = json_clean(reply_content)
        msg = self.session.send(stream, 'inspect_reply',
                                reply_content, parent, ident)
        self.log.debug("%s", msg)

    def do_inspect(self, code, cursor_pos, detail_level=0):
        """Override in subclasses to allow introspection.
        """
        return {'status': 'ok', 'data':{}, 'metadata':{}, 'found':False}

    def history_request(self, stream, ident, parent):
        content = parent['content']

        reply_content = self.do_history(**content)

        reply_content = json_clean(reply_content)
        msg = self.session.send(stream, 'history_reply',
                                reply_content, parent, ident)
        self.log.debug("%s", msg)

    def do_history(self, hist_access_type, output, raw, session=None, start=None,
                   stop=None, n=None, pattern=None, unique=False):
        """Override in subclasses to access history.
        """
        return {'history': []}

    def connect_request(self, stream, ident, parent):
        if self._recorded_ports is not None:
            content = self._recorded_ports.copy()
        else:
            content = {}
        msg = self.session.send(stream, 'connect_reply',
                                content, parent, ident)
        self.log.debug("%s", msg)

    @property
    def kernel_info(self):
        return {
            'protocol_version': release.kernel_protocol_version,
            'implementation': self.implementation,
            'implementation_version': self.implementation_version,
            'language_info': self.language_info,
            'banner': self.banner,
            'help_links': self.help_links,
        }

    def kernel_info_request(self, stream, ident, parent):
        msg = self.session.send(stream, 'kernel_info_reply',
                                self.kernel_info, parent, ident)
        self.log.debug("%s", msg)

    def shutdown_request(self, stream, ident, parent):
        content = self.do_shutdown(parent['content']['restart'])
        self.session.send(stream, u'shutdown_reply', content, parent, ident=ident)
        # same content, but different msg_id for broadcasting on IOPub
        self._shutdown_message = self.session.msg(u'shutdown_reply',
                                                  content, parent
        )

        self._at_shutdown()
        # call sys.exit after a short delay
        loop = ioloop.IOLoop.instance()
        loop.add_timeout(time.time()+0.1, loop.stop)

    def do_shutdown(self, restart):
        """Override in subclasses to do things when the frontend shuts down the
        kernel.
        """
        return {'status': 'ok', 'restart': restart}
    
    def is_complete_request(self, stream, ident, parent):
        content = parent['content']
        code = content['code']
        
        reply_content = self.do_is_complete(code)
        reply_content = json_clean(reply_content)
        reply_msg = self.session.send(stream, 'is_complete_reply',
                                           reply_content, parent, ident)
        self.log.debug("%s", reply_msg)

    def do_is_complete(self, code):
        """Override in subclasses to find completions.
        """
        return {'status' : 'unknown',
                }

    #---------------------------------------------------------------------------
    # Engine methods
    #---------------------------------------------------------------------------

    def apply_request(self, stream, ident, parent):
        try:
            content = parent[u'content']
            bufs = parent[u'buffers']
            msg_id = parent['header']['msg_id']
        except:
            self.log.error("Got bad msg: %s", parent, exc_info=True)
            return

        md = self._make_metadata(parent['metadata'])

        reply_content, result_buf = self.do_apply(content, bufs, msg_id, md)

        # put 'ok'/'error' status in header, for scheduler introspection:
        md['status'] = reply_content['status']

        # flush i/o
        sys.stdout.flush()
        sys.stderr.flush()
        
        self.session.send(stream, u'apply_reply', reply_content,
                    parent=parent, ident=ident,buffers=result_buf, metadata=md)

    def do_apply(self, content, bufs, msg_id, reply_metadata):
        """Override in subclasses to support the IPython parallel framework.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    # Control messages
    #---------------------------------------------------------------------------

    def abort_request(self, stream, ident, parent):
        """abort a specific msg by id"""
        msg_ids = parent['content'].get('msg_ids', None)
        if isinstance(msg_ids, string_types):
            msg_ids = [msg_ids]
        if not msg_ids:
            self._abort_queues()
        for mid in msg_ids:
            self.aborted.add(str(mid))

        content = dict(status='ok')
        reply_msg = self.session.send(stream, 'abort_reply', content=content,
                parent=parent, ident=ident)
        self.log.debug("%s", reply_msg)

    def clear_request(self, stream, idents, parent):
        """Clear our namespace."""
        content = self.do_clear()
        self.session.send(stream, 'clear_reply', ident=idents, parent=parent,
                content = content)

    def do_clear(self):
        """Override in subclasses to clear the namespace
        
        This is only required for IPython.parallel.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _topic(self, topic):
        """prefixed topic for IOPub messages"""
        if self.int_id >= 0:
            base = "engine.%i" % self.int_id
        else:
            base = "kernel.%s" % self.ident
        
        return py3compat.cast_bytes("%s.%s" % (base, topic))
    
    def _abort_queues(self):
        for stream in self.shell_streams:
            if stream:
                self._abort_queue(stream)

    def _abort_queue(self, stream):
        poller = zmq.Poller()
        poller.register(stream.socket, zmq.POLLIN)
        while True:
            idents,msg = self.session.recv(stream, zmq.NOBLOCK, content=True)
            if msg is None:
                return

            self.log.info("Aborting:")
            self.log.info("%s", msg)
            msg_type = msg['header']['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'

            status = {'status' : 'aborted'}
            md = {'engine' : self.ident}
            md.update(status)
            reply_msg = self.session.send(stream, reply_type, metadata=md,
                        content=status, parent=msg, ident=idents)
            self.log.debug("%s", reply_msg)
            # We need to wait a bit for requests to come in. This can probably
            # be set shorter for true asynchronous clients.
            poller.poll(50)


    def _no_raw_input(self):
        """Raise StdinNotImplentedError if active frontend doesn't support
        stdin."""
        raise StdinNotImplementedError("raw_input was called, but this "
                                       "frontend does not support stdin.") 
    
    def getpass(self, prompt=''):
        """Forward getpass to frontends
        
        Raises
        ------
        StdinNotImplentedError if active frontend doesn't support stdin.
        """
        if not self._allow_stdin:
            raise StdinNotImplementedError(
                "getpass was called, but this frontend does not support input requests."
            )
        return self._input_request(prompt,
            self._parent_ident,
            self._parent_header,
            password=True,
        )
    
    def raw_input(self, prompt=''):
        """Forward raw_input to frontends
        
        Raises
        ------
        StdinNotImplentedError if active frontend doesn't support stdin.
        """
        if not self._allow_stdin:
            raise StdinNotImplementedError(
                "raw_input was called, but this frontend does not support input requests."
            )
        return self._input_request(prompt,
            self._parent_ident,
            self._parent_header,
            password=False,
        )
    
    def _input_request(self, prompt, ident, parent, password=False):
        # Flush output before making the request.
        sys.stderr.flush()
        sys.stdout.flush()
        # flush the stdin socket, to purge stale replies
        while True:
            try:
                self.stdin_socket.recv_multipart(zmq.NOBLOCK)
            except zmq.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    break
                else:
                    raise
        
        # Send the input request.
        content = json_clean(dict(prompt=prompt, password=password))
        self.session.send(self.stdin_socket, u'input_request', content, parent,
                          ident=ident)

        # Await a response.
        while True:
            try:
                ident, reply = self.session.recv(self.stdin_socket, 0)
            except Exception:
                self.log.warn("Invalid Message:", exc_info=True)
            except KeyboardInterrupt:
                # re-raise KeyboardInterrupt, to truncate traceback
                raise KeyboardInterrupt
            else:
                break
        try:
            value = py3compat.unicode_to_str(reply['content']['value'])
        except:
            self.log.error("Bad input_reply: %s", parent)
            value = ''
        if value == '\x04':
            # EOF
            raise EOFError
        return value

    def _at_shutdown(self):
        """Actions taken at shutdown by the kernel, called by python's atexit.
        """
        # io.rprint("Kernel at_shutdown") # dbg
        if self._shutdown_message is not None:
            self.session.send(self.iopub_socket, self._shutdown_message, ident=self._topic('shutdown'))
            self.log.debug("%s", self._shutdown_message)
        [ s.flush(zmq.POLLOUT) for s in self.shell_streams ]
