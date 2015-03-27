"""Wrappers for forwarding stdout/stderr over zmq"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import threading
import time
import uuid
from io import StringIO, UnsupportedOperation

import zmq
from zmq.eventloop.ioloop import IOLoop

from .session import extract_header

from IPython.utils import py3compat
from IPython.utils.py3compat import unicode_type
from IPython.utils.warn import warn

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

MASTER = 0
CHILD = 1

#-----------------------------------------------------------------------------
# Stream classes
#-----------------------------------------------------------------------------

class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    # The time interval between automatic flushes, in seconds.
    _subprocess_flush_limit = 256
    flush_interval = 0.05
    topic=None

    def __init__(self, session, pub_socket, name, pipe=True):
        self.encoding = 'UTF-8'
        self.session = session
        self.pub_socket = pub_socket
        self.name = name
        self.topic = b'stream.' + py3compat.cast_bytes(name)
        self.parent_header = {}
        self._new_buffer()
        self._buffer_lock = threading.Lock()
        self._master_pid = os.getpid()
        self._master_thread = threading.current_thread().ident
        self._pipe_pid = os.getpid()
        self._pipe_flag = pipe
        if pipe:
            self._setup_pipe_in()
    
    def _setup_pipe_in(self):
        """setup listening pipe for subprocesses"""
        ctx = self.pub_socket.context
        
        # use UUID to authenticate pipe messages
        self._pipe_uuid = uuid.uuid4().bytes
        
        self._pipe_in = ctx.socket(zmq.PULL)
        self._pipe_in.linger = 0
        try:
            self._pipe_port = self._pipe_in.bind_to_random_port("tcp://127.0.0.1")
        except zmq.ZMQError as e:
            warn("Couldn't bind IOStream to 127.0.0.1: %s" % e +
                "\nsubprocess output will be unavailable."
            )
            self._pipe_flag = False
            self._pipe_in.close()
            del self._pipe_in
            return
        self._pipe_poller = zmq.Poller()
        self._pipe_poller.register(self._pipe_in, zmq.POLLIN)
        if IOLoop.initialized():
            # subprocess flush should trigger flush
            # if kernel is idle
            IOLoop.instance().add_handler(self._pipe_in,
                lambda s, event: self.flush(),
                IOLoop.READ,
            )
    
    def _setup_pipe_out(self):
        # must be new context after fork
        ctx = zmq.Context()
        self._pipe_pid = os.getpid()
        self._pipe_out = ctx.socket(zmq.PUSH)
        self._pipe_out_lock = threading.Lock()
        self._pipe_out.connect("tcp://127.0.0.1:%i" % self._pipe_port)
    
    def _is_master_process(self):
        return os.getpid() == self._master_pid
    
    def _is_master_thread(self):
        return threading.current_thread().ident == self._master_thread
    
    def _have_pipe_out(self):
        return os.getpid() == self._pipe_pid

    def _check_mp_mode(self):
        """check for forks, and switch to zmq pipeline if necessary"""
        if not self._pipe_flag or self._is_master_process():
            return MASTER
        else:
            if not self._have_pipe_out():
                self._flush_buffer()
                # setup a new out pipe
                self._setup_pipe_out()
            return CHILD

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    @property
    def closed(self):
        return self.pub_socket is None

    def _flush_from_subprocesses(self):
        """flush possible pub data from subprocesses into my buffer"""
        if not self._pipe_flag or not self._is_master_process():
            return
        for i in range(self._subprocess_flush_limit):
            if self._pipe_poller.poll(0):
                msg = self._pipe_in.recv_multipart()
                if msg[0] != self._pipe_uuid:
                    continue
                else:
                    self._buffer.write(msg[1].decode(self.encoding, 'replace'))
                    # this always means a flush,
                    # so reset our timer
                    self._start = 0
            else:
                break
    
    def _schedule_flush(self):
        """schedule a flush in the main thread
        
        only works with a tornado/pyzmq eventloop running
        """
        if IOLoop.initialized():
            IOLoop.instance().add_callback(self.flush)
        else:
            # no async loop, at least force the timer
            self._start = 0
    
    def flush(self):
        """trigger actual zmq send"""
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        
        mp_mode = self._check_mp_mode()
        
        if mp_mode != CHILD:
            # we are master
            if not self._is_master_thread():
                # sub-threads must not trigger flush directly,
                # but at least they can schedule an async flush, or force the timer.
                self._schedule_flush()
                return
            
            self._flush_from_subprocesses()
            data = self._flush_buffer()
            
            if data:
                content = {u'name':self.name, u'text':data}
                msg = self.session.send(self.pub_socket, u'stream', content=content,
                                       parent=self.parent_header, ident=self.topic)
            
                if hasattr(self.pub_socket, 'flush'):
                    # socket itself has flush (presumably ZMQStream)
                    self.pub_socket.flush()
        else:
            with self._pipe_out_lock:
                string = self._flush_buffer()
                tracker = self._pipe_out.send_multipart([
                    self._pipe_uuid,
                    string.encode(self.encoding, 'replace'),
                ], copy=False, track=True)
                try:
                    tracker.wait(1)
                except:
                    pass

    def isatty(self):
        return False

    def __next__(self):
        raise IOError('Read not supported on a write only stream.')

    if not py3compat.PY3:
        next = __next__

    def read(self, size=-1):
        raise IOError('Read not supported on a write only stream.')

    def readline(self, size=-1):
        raise IOError('Read not supported on a write only stream.')
    
    def fileno(self):
        raise UnsupportedOperation("IOStream has no fileno.")

    def write(self, string):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            # Make sure that we're handling unicode
            if not isinstance(string, unicode_type):
                string = string.decode(self.encoding, 'replace')
            
            is_child = (self._check_mp_mode() == CHILD)
            self._buffer.write(string)
            if is_child:
                # newlines imply flush in subprocesses
                # mp.Pool cannot be trusted to flush promptly (or ever),
                # and this helps.
                if '\n' in string:
                    self.flush()
            # do we want to check subprocess flushes on write?
            # self._flush_from_subprocesses()
            current_time = time.time()
            if self._start < 0:
                self._start = current_time
            elif current_time - self._start > self.flush_interval:
                self.flush()

    def writelines(self, sequence):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            for string in sequence:
                self.write(string)

    def _flush_buffer(self):
        """clear the current buffer and return the current buffer data"""
        data = u''
        if self._buffer is not None:
            data = self._buffer.getvalue()
            self._buffer.close()
        self._new_buffer()
        return data
    
    def _new_buffer(self):
        self._buffer = StringIO()
        self._start = -1
