import sys
import time
import os
import threading
import uuid
from io import StringIO

import zmq

from session import extract_header, Message

from IPython.utils import io, text
from IPython.utils import py3compat

import multiprocessing as mp
# import multiprocessing.sharedctypes as mpshc
from ctypes import c_bool
#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

MASTER_NO_CHILDREN = 0
MASTER_WITH_CHILDREN = 1
CHILD = 2

#-----------------------------------------------------------------------------
# Stream classes
#-----------------------------------------------------------------------------

class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    # The time interval between automatic flushes, in seconds.
    flush_interval = 0.05
    topic=None

    def __init__(self, session, pub_socket, name):
        self.encoding = 'UTF-8'
        self.session = session
        self.pub_socket = pub_socket
        self.name = name
        self.parent_header = {}
        self._new_buffer()
        self._found_newprocess = 0
        self._buffer_lock = threading.Lock()
        self._master_pid = os.getpid()
        self._master_thread = threading.current_thread().ident
        self._pipe_pid = os.getpid()
        self._setup_pipe_in()
    
    def _setup_pipe_in(self):
        """setup listening pipe for subprocesses"""
        ctx = self.pub_socket.context
        
        # use UUID to authenticate pipe messages
        self._pipe_uuid = uuid.uuid4().bytes
        
        self._pipe_in = ctx.socket(zmq.PULL)
        self._pipe_in.linger = 0
        self._pipe_port = self._pipe_in.bind_to_random_port("tcp://127.0.0.1")
        self._pipe_poller = zmq.Poller()
        self._pipe_poller.register(self._pipe_in, zmq.POLLIN)
    
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
        if self._is_master_process():
            if self._found_newprocess:
                return MASTER_WITH_CHILDREN
            else:
                return MASTER_NO_CHILDREN
        else:
            if not self._have_pipe_out():
                # setup a new out pipe
                self._setup_pipe_out()
            return CHILD

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    def _flush_from_subprocesses(self):
        """flush possible pub data from subprocesses into my buffer"""
        if not self._is_master_process():
            return
        for i in range(100):
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
    
    def flush(self):
        """trigger actual zmq send"""
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        
        mp_mode = self._check_mp_mode()
        
        if mp_mode != CHILD:
            # we are master
            if not self._is_master_thread():
                # sub-threads must not trigger flush,
                # but at least they can force the timer.
                self._start = 0
                return
            
            self._flush_from_subprocesses()
            data = self._flush_buffer()
            
            if data:
                content = {u'name':self.name, u'data':data}
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
                tracker.wait(1)

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

    def write(self, string):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            # Make sure that we're handling unicode
            if not isinstance(string, unicode):
                string = string.decode(self.encoding, 'replace')
            self._buffer.write(string)
            self._check_mp_mode()
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
        
