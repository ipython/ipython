import sys
import time
from cStringIO import StringIO

from session import extract_header, Message

#-----------------------------------------------------------------------------
# Stream classes
#-----------------------------------------------------------------------------

class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    # The time interval between automatic flushes, in seconds.
    flush_interval = 0.05

    def __init__(self, session, pub_socket, name):
        self.session = session
        self.pub_socket = pub_socket
        self.name = name
        self.parent_header = {}
        self._new_buffer()

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    def flush(self):
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        else:
            data = self._buffer.getvalue()
            if data:
                content = {u'name':self.name, u'data':data}
                msg = self.session.msg(u'stream', content=content,
                                       parent=self.parent_header)
                print>>sys.__stdout__, Message(msg)
                self.pub_socket.send_json(msg)
                
                self._buffer.close()
                self._new_buffer()

    def isatty(self):
        return False

    def next(self):
        raise IOError('Read not supported on a write only stream.')

    def read(self, size=-1):
        raise IOError('Read not supported on a write only stream.')

    def readline(self, size=-1):
        raise IOError('Read not supported on a write only stream.')

    def write(self, string):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            self._buffer.write(string)
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
                self.write(string)

    def _new_buffer(self):
        self._buffer = StringIO()
        self._start = -1