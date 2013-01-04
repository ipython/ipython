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
        self._found_newprocess = threading.Event()
        self._buffer_lock = threading.Lock()
        self._master_pid = os.getpid()
        self._master_thread = threading.current_thread().ident
        self._pipe_pid = os.getpid()
        self._setup_pipe_in()
    
    def _setup_pipe_in(self):
        """setup listening pipe for subprocesses"""
        ctx = self._pipe_ctx = zmq.Context()
        
        # signal pair for terminating background thread
        self._pipe_signaler = ctx.socket(zmq.PAIR)
        self._pipe_signalee = ctx.socket(zmq.PAIR)
        self._pipe_signaler.bind("inproc://ostream_pipe")
        self._pipe_signalee.connect("inproc://ostream_pipe")
        # thread event to signal cleanup is done
        self._pipe_done = threading.Event() 
        
        # use UUID to authenticate pipe messages
        self._pipe_uuid = uuid.uuid4().bytes
        
        self._pipe_thread = threading.Thread(target=self._pipe_main)
        self._pipe_thread.start()
    
    def _setup_pipe_out(self):
        # must be new context after fork
        ctx = zmq.Context()
        self._pipe_pid = os.getpid()
        self._pipe_out = ctx.socket(zmq.PUSH)
        self._pipe_out_lock = threading.Lock()
        self._pipe_out.connect("tcp://127.0.0.1:%i" % self._pipe_port)
    
    def _pipe_main(self):
        """eventloop for receiving"""
        ctx = self._pipe_ctx
        self._pipe_in = ctx.socket(zmq.PULL)
        self._pipe_port = self._pipe_in.bind_to_random_port("tcp://127.0.0.1")
        poller = zmq.Poller()
        poller.register(self._pipe_signalee, zmq.POLLIN)
        poller.register(self._pipe_in, zmq.POLLIN)
        while True:
            if not self._is_master_process():
                return
            try:
                events = dict(poller.poll(1000))
            except zmq.ZMQError:
                # should only be triggered by process-ending cleanup
                return
            
            if self._pipe_signalee in events:
                break
            if self._pipe_in in events:
                msg = self._pipe_in.recv_multipart()
                if msg[0] != self._pipe_uuid:
                    # message not authenticated
                    continue
                self._found_newprocess.set()
                text = msg[1].decode(self.encoding, 'replace')
                with self._buffer_lock:
                    self._buffer.write(text)
                    if self._start < 0:
                        self._start = time.time()
        
        # wrap it up
        self._pipe_signaler.close()
        self._pipe_signalee.close()
        self._pipe_in.close()
        self._pipe_ctx.term()
        self._pipe_done.set()
    
    
    def __del__(self):
        if not self._is_master_process():
            return
        self._pipe_signaler.send(b'die')
        self._pipe_done.wait(10)
    
    def _is_master_process(self):
        return os.getpid() == self._master_pid
    
    def _is_master_thread(self):
        return threading.current_thread().ident == self._master_thread
    
    def _have_pipe_out(self):
        return os.getpid() == self._pipe_pid

    def _check_mp_mode(self):
        """check for forks, and switch to zmq pipeline if necessary"""
        if self._is_master_process():
            if self._found_newprocess.is_set():
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

    def flush(self):
        """trigger actual zmq send"""
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        else:
            if self._is_master_process():
                if not self._is_master_thread():
                    # sub-threads mustn't trigger flush,
                    # but at least they can force the timer.
                    self._start = 0
                data = u''
                # obtain data
                if self._check_mp_mode(): # multiprocess, needs a lock
                    with self._buffer_lock:
                        data = self._buffer.getvalue()
                        self._buffer.close()
                        self._new_buffer()
                else: # single process mode
                    data = self._buffer.getvalue()
                    self._buffer.close()
                    self._new_buffer()

                if data:
                    content = {u'name':self.name, u'data':data}
                    msg = self.session.send(self.pub_socket, u'stream', content=content,
                                           parent=self.parent_header, ident=self.topic)

                    if hasattr(self.pub_socket, 'flush'):
                        # socket itself has flush (presumably ZMQStream)
                        self.pub_socket.flush()
            else:
                self._check_mp_mode()
                with self._pipe_out_lock:
                    tracker = self._pipe_out.send(b'', copy=False, track=True)
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
            
            mp_mode = self._check_mp_mode()
            if mp_mode == CHILD:
                with self._pipe_out_lock:
                    self._pipe_out.send_multipart([
                        self._pipe_uuid,
                        string.encode(self.encoding, 'replace'),
                    ])
                return
            elif mp_mode == MASTER_NO_CHILDREN:
                self._buffer.write(string)
            elif mp_mode == MASTER_WITH_CHILDREN:
                with self._buffer_lock:
                    self._buffer.write(string)

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

    def _new_buffer(self):
        self._buffer = StringIO()
        self._start = -1
