import sys
import time
import os
from io import StringIO

from session import extract_header, Message

from IPython.utils import io, text
from IPython.utils import py3compat

import multiprocessing as mp
import multiprocessing.sharedctypes as mpshc
from ctypes import c_bool
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
    topic=None

    def __init__(self, session, pub_socket, name):
        self.encoding = 'UTF-8'
        self.session = session
        self.pub_socket = pub_socket
        self.name = name
        self.parent_header = {}
        self._new_buffer()
        self._manager = mp.Manager()
        #use sharectype here so it don't have to hit the manager
        #no synchronize needed either(right?). Just a flag telling the master
        #to switch the buffer to que
        self._found_newprocess = mpshc.RawValue(c_bool, False)
        self._que_buffer = self._manager.Queue()
        self._que_lock = self._manager.Lock()
        self._masterpid = os.getpid()
        self._master_has_switched = False

    def _switch_to_que(self):
        #should only be called on master process
        #don't clear the que before putting data in since
        #child process might have put something in the que before the
        #master know it.
        self._que_buffer.put(self._buffer.getvalue())
        self._new_buffer()
        self._start = -1

    def _is_master_process(self):
        return os.getpid()==self._masterpid

    def _debug_print(self,s):
        sys.__stdout__.write(s+'\n')
        sys.__stdout__.flush()

    def _check_mp_mode(self):
        """check multiprocess and switch to que if necessary"""
        if not self._found_newprocess.value:
            if not self._is_master_process():
                self._found_newprocess.value = True
        elif self._found_newprocess.value and not self._master_has_switched:

            #switch to que if it has not been switch
            if self._is_master_process():
                self._switch_to_que()
                self._master_has_switched = True

        return self._found_newprocess.value


    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    def flush(self):
        #io.rprint('>>>flushing output buffer: %s<<<' % self.name)  # dbg

        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        else:
            if self._is_master_process():
                data = u''
                #obtain data
                if self._check_mp_mode():#multiprocess
                    with self._que_lock:
                        while not self._que_buffer.empty():
                            data += self._que_buffer.get()
                else:#single process mode
                    data = self._buffer.getvalue()

                if data:
                    content = {u'name':self.name, u'data':data}
                    msg = self.session.send(self.pub_socket, u'stream', content=content,
                                           parent=self.parent_header, ident=self.topic)

                    if hasattr(self.pub_socket, 'flush'):
                        # socket itself has flush (presumably ZMQStream)
                        self.pub_socket.flush()
                    self._buffer.close()
                    self._new_buffer()
            else:
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

    def write(self, string):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            # Make sure that we're handling unicode
            if not isinstance(string, unicode):
                string = string.decode(self.encoding, 'replace')

            if self._check_mp_mode(): #multi process mode
                with self._que_lock:
                    self._que_buffer.put(string)
            else: #sigle process mode
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
