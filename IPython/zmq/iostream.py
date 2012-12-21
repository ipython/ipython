import os
import sys
import time

from session import extract_header, Message

from IPython.utils import io, text
from IPython.utils import py3compat

from multiprocessing import Manager

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Stream classes
#-----------------------------------------------------------------------------

class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    # The time interval between automatic flushes, in seconds.
    flush_interval = 0.05
    topic = None

    def __init__(self, session, pub_socket, name, pid=None):
        self.encoding = 'UTF-8'
        self.session = session
        self.pub_socket = pub_socket
        self.name = name
        self.parent_header = {}
        self.master_pid = self.getpid() if pid is None else pid
        self._manager = Manager()
        self._buffer = self._manager.Queue()
        self._start = -1

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    def flush(self):
        #io.rprint('>>>flushing output buffer: %s<<<' % self.name)  # dbg
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        elif self.getpid() == self.master_pid:#only flush on master process
            data = ''
            while not self._buffer.empty():
                data += self._buffer.get()
            if data:
                content = {u'name':self.name, u'data':data}
                msg = self.session.send(self.pub_socket, u'stream', content=content,
                                       parent=self.parent_header, ident=self.topic)

                if hasattr(self.pub_socket, 'flush'):
                    # socket itself has flush (presumably ZMQStream)
                    self.pub_socket.flush()
        else:
            pass#on a forked process don't flush

    def getpid(self):
        p = getattr(os,'getpid',None)
        if p is not None:
            return p()
        else:#windows
            return None

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

            self._buffer.put(string)
            current_time = time.time()
            if self._start <= 0:
                self._start = current_time
            elif current_time - self._start > self.flush_interval:
                self.flush()

    def writelines(self, sequence):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            for string in sequence:
                self._buffer.put(string)
