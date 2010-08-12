#!/usr/bin/env python
"""A simple interactive kernel that talks to a frontend over 0MQ.

Things to do:

* Finish implementing `raw_input`.
* Implement `set_parent` logic. Right before doing exec, the Kernel should
  call set_parent on all the PUB objects with the message about to be executed.
* Implement random port and security key logic.
* Implement control messages.
* Implement event loop and poll version.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports.
import __builtin__
from code import CommandCompiler
from cStringIO import StringIO
import os
import sys
from threading import Thread
import time
import traceback

# System library imports.
import zmq

# Local imports.
from IPython.external.argparse import ArgumentParser
from session import Session, Message, extract_header
from completer import KernelCompleter

#-----------------------------------------------------------------------------
# Kernel and stream classes
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


class DisplayHook(object):

    def __init__(self, session, pub_socket):
        self.session = session
        self.pub_socket = pub_socket
        self.parent_header = {}

    def __call__(self, obj):
        if obj is not None:
            __builtin__._ = obj
            msg = self.session.msg(u'pyout', {u'data':repr(obj)},
                                   parent=self.parent_header)
            self.pub_socket.send_json(msg)

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)


class Kernel(object):

    # The global kernel instance.
    _kernel = None

    # Maps user-friendly backend names to matplotlib backend identifiers.
    _pylab_map = { 'tk': 'TkAgg',
                   'gtk': 'GTKAgg',
                   'wx': 'WXAgg',
                   'qt': 'Qt4Agg', # qt3 not supported
                   'qt4': 'Qt4Agg',
                   'payload-svg' : \
                       'module://IPython.zmq.pylab.backend_payload_svg' }

    #---------------------------------------------------------------------------
    # Kernel interface
    #---------------------------------------------------------------------------

    def __init__(self, session, reply_socket, pub_socket, req_socket):
        self.session = session
        self.reply_socket = reply_socket
        self.pub_socket = pub_socket
        self.req_socket = req_socket
        self.user_ns = {}
        self.history = []
        self.compiler = CommandCompiler()
        self.completer = KernelCompleter(self.user_ns)

        # Protected variables.
        self._exec_payload = {}
        
        # Build dict of handlers for message types
        msg_types = [ 'execute_request', 'complete_request', 
                      'object_info_request' ]
        self.handlers = {}
        for msg_type in msg_types:
            self.handlers[msg_type] = getattr(self, msg_type)

    def add_exec_payload(self, key, value):
        """ Adds a key/value pair to the execute payload.
        """
        self._exec_payload[key] = value

    def activate_pylab(self, backend=None, import_all=True):
        """ Activates pylab in this kernel's namespace.

        Parameters:
        -----------
        backend : str, optional
            A valid backend name.

        import_all : bool, optional
            If true, an 'import *' is done from numpy and pylab.
        """
        # FIXME: This is adapted from IPython.lib.pylabtools.pylab_activate.
        #        Common funtionality should be refactored.

        # We must set the desired backend before importing pylab.
        import matplotlib
        if backend:
            backend_id = self._pylab_map[backend]
            if backend_id.startswith('module://'):
                # Work around bug in matplotlib: matplotlib.use converts the
                # backend_id to lowercase even if a module name is specified!
                matplotlib.rcParams['backend'] = backend_id
            else:
                matplotlib.use(backend_id)

        # Import numpy as np/pyplot as plt are conventions we're trying to
        # somewhat standardize on. Making them available to users by default
        # will greatly help this.
        exec ("import numpy\n"
              "import matplotlib\n"
              "from matplotlib import pylab, mlab, pyplot\n"
              "np = numpy\n"
              "plt = pyplot\n"
              ) in self.user_ns

        if import_all:
            exec("from matplotlib.pylab import *\n"
                 "from numpy import *\n") in self.user_ns

        matplotlib.interactive(True)

    @classmethod
    def get_kernel(cls):
        """ Return the global kernel instance or raise a RuntimeError if it does
        not exist.
        """
        if cls._kernel is None:
            raise RuntimeError("Kernel not started!")
        else:
            return cls._kernel

    def start(self):
        """ Start the kernel main loop.
        """
        # Set the global kernel instance.
        Kernel._kernel = self

        while True:
            ident = self.reply_socket.recv()
            assert self.reply_socket.rcvmore(), "Missing message part."
            msg = self.reply_socket.recv_json()
            omsg = Message(msg)
            print>>sys.__stdout__
            print>>sys.__stdout__, omsg
            handler = self.handlers.get(omsg.msg_type, None)
            if handler is None:
                print >> sys.__stderr__, "UNKNOWN MESSAGE TYPE:", omsg
            else:
                handler(ident, omsg)

    #---------------------------------------------------------------------------
    # Kernel request handlers
    #---------------------------------------------------------------------------

    def execute_request(self, ident, parent):
        try:
            code = parent[u'content'][u'code']
        except:
            print>>sys.__stderr__, "Got bad msg: "
            print>>sys.__stderr__, Message(parent)
            return
        pyin_msg = self.session.msg(u'pyin',{u'code':code}, parent=parent)
        self.pub_socket.send_json(pyin_msg)

        # Clear the execute payload from the last request.
        self._exec_payload = {}

        try:
            comp_code = self.compiler(code, '<zmq-kernel>')

            # Replace raw_input. Note that is not sufficient to replace 
            # raw_input in the user namespace.
            raw_input = lambda prompt='': self._raw_input(prompt, ident, parent)
            __builtin__.raw_input = raw_input

            # Configure the display hook.
            sys.displayhook.set_parent(parent)

            exec comp_code in self.user_ns, self.user_ns
        except:
            result = u'error'
            etype, evalue, tb = sys.exc_info()
            tb = traceback.format_exception(etype, evalue, tb)
            exc_content = {
                u'status' : u'error',
                u'traceback' : tb,
                u'ename' : unicode(etype.__name__),
                u'evalue' : unicode(evalue)
            }
            exc_msg = self.session.msg(u'pyerr', exc_content, parent)
            self.pub_socket.send_json(exc_msg)
            reply_content = exc_content
        else:
            reply_content = { 'status' : 'ok', 'payload' : self._exec_payload }
            
        # Flush output before sending the reply.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the reply.
        reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        print>>sys.__stdout__, Message(reply_msg)
        self.reply_socket.send(ident, zmq.SNDMORE)
        self.reply_socket.send_json(reply_msg)
        if reply_msg['content']['status'] == u'error':
            self._abort_queue()

    def complete_request(self, ident, parent):
        comp = self.completer.complete(parent.content.line, parent.content.text)
        matches = {'matches' : comp, 'status' : 'ok'}
        completion_msg = self.session.send(self.reply_socket, 'complete_reply',
                                           matches, parent, ident)
        print >> sys.__stdout__, completion_msg

    def object_info_request(self, ident, parent):
        context = parent['content']['oname'].split('.')
        object_info = self._object_info(context)
        msg = self.session.send(self.reply_socket, 'object_info_reply',
                                object_info, parent, ident)
        print >> sys.__stdout__, msg

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _abort_queue(self):
        while True:
            try:
                ident = self.reply_socket.recv(zmq.NOBLOCK)
            except zmq.ZMQError, e:
                if e.errno == zmq.EAGAIN:
                    break
            else:
                assert self.reply_socket.rcvmore(), "Missing message part."
                msg = self.reply_socket.recv_json()
            print>>sys.__stdout__, "Aborting:"
            print>>sys.__stdout__, Message(msg)
            msg_type = msg['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            reply_msg = self.session.msg(reply_type, {'status':'aborted'}, msg)
            print>>sys.__stdout__, Message(reply_msg)
            self.reply_socket.send(ident,zmq.SNDMORE)
            self.reply_socket.send_json(reply_msg)
            # We need to wait a bit for requests to come in. This can probably
            # be set shorter for true asynchronous clients.
            time.sleep(0.1)

    def _raw_input(self, prompt, ident, parent):
        # Flush output before making the request.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the input request.
        content = dict(prompt=prompt)
        msg = self.session.msg(u'input_request', content, parent)
        self.req_socket.send_json(msg)

        # Await a response.
        reply = self.req_socket.recv_json()
        try:
            value = reply['content']['value']
        except:
            print>>sys.__stderr__, "Got bad raw_input reply: "
            print>>sys.__stderr__, Message(parent)
            value = ''
        return value

    def _object_info(self, context):
        symbol, leftover = self._symbol_from_context(context)
        if symbol is not None and not leftover:
            doc = getattr(symbol, '__doc__', '')
        else:
            doc = ''
        object_info = dict(docstring = doc)
        return object_info

    def _symbol_from_context(self, context):
        if not context:
            return None, context

        base_symbol_string = context[0]
        symbol = self.user_ns.get(base_symbol_string, None)
        if symbol is None:
            symbol = __builtin__.__dict__.get(base_symbol_string, None)
        if symbol is None:
            return None, context

        context = context[1:]
        for i, name in enumerate(context):
            new_symbol = getattr(symbol, name, None)
            if new_symbol is None:
                return symbol, context[i:]
            else:
                symbol = new_symbol

        return symbol, []

#-----------------------------------------------------------------------------
# Kernel main and launch functions
#-----------------------------------------------------------------------------

class ExitPollerUnix(Thread):
    """ A Unix-specific daemon thread that terminates the program immediately 
    when the parent process no longer exists.
    """

    def __init__(self):
        super(ExitPollerUnix, self).__init__()
        self.daemon = True
    
    def run(self):
        # We cannot use os.waitpid because it works only for child processes.
        from errno import EINTR
        while True:
            try:
                if os.getppid() == 1:
                    os._exit(1)
                time.sleep(1.0)
            except OSError, e:
                if e.errno == EINTR:
                    continue
                raise

class ExitPollerWindows(Thread):
    """ A Windows-specific daemon thread that terminates the program immediately
    when a Win32 handle is signaled.
    """ 
    
    def __init__(self, handle):
        super(ExitPollerWindows, self).__init__()
        self.daemon = True
        self.handle = handle

    def run(self):
        from _subprocess import WaitForSingleObject, WAIT_OBJECT_0, INFINITE
        result = WaitForSingleObject(self.handle, INFINITE)
        if result == WAIT_OBJECT_0:
            os._exit(1)


def bind_port(socket, ip, port):
    """ Binds the specified ZMQ socket. If the port is zero, a random port is
    chosen. Returns the port that was bound.
    """
    connection = 'tcp://%s' % ip
    if port <= 0:
        port = socket.bind_to_random_port(connection)
    else:
        connection += ':%i' % port
        socket.bind(connection)
    return port


def main():
    """ Main entry point for launching a kernel.
    """
    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument('--ip', type=str, default='127.0.0.1',
                        help='set the kernel\'s IP address [default: local]')
    parser.add_argument('--xrep', type=int, metavar='PORT', default=0,
                        help='set the XREP channel port [default: random]')
    parser.add_argument('--pub', type=int, metavar='PORT', default=0,
                        help='set the PUB channel port [default: random]')
    parser.add_argument('--req', type=int, metavar='PORT', default=0,
                        help='set the REQ channel port [default: random]')
    if sys.platform == 'win32':
        parser.add_argument('--parent', type=int, metavar='HANDLE', 
                            default=0, help='kill this process if the process '
                            'with HANDLE dies')
    else:
        parser.add_argument('--parent', action='store_true', 
                            help='kill this process if its parent dies')
    parser.add_argument('--pylab', type=str, metavar='GUI', nargs='?', 
                        const='auto', help = \
        "Pre-load matplotlib and numpy for interactive use. If GUI is not \
given, the GUI backend is matplotlib's, otherwise use one of: \
['tk', 'gtk', 'qt', 'wx', 'payload-svg'].")

    namespace = parser.parse_args()

    # Create a context, a session, and the kernel sockets.
    print >>sys.__stdout__, "Starting the kernel..."
    context = zmq.Context()
    session = Session(username=u'kernel')

    reply_socket = context.socket(zmq.XREP)
    xrep_port = bind_port(reply_socket, namespace.ip, namespace.xrep)
    print >>sys.__stdout__, "XREP Channel on port", xrep_port

    pub_socket = context.socket(zmq.PUB)
    pub_port = bind_port(pub_socket, namespace.ip, namespace.pub)
    print >>sys.__stdout__, "PUB Channel on port", pub_port

    req_socket = context.socket(zmq.XREQ)
    req_port = bind_port(req_socket, namespace.ip, namespace.req)
    print >>sys.__stdout__, "REQ Channel on port", req_port

    # Create the kernel.
    kernel = Kernel(session, reply_socket, pub_socket, req_socket)

    # Set up pylab, if necessary.
    if namespace.pylab:
        if namespace.pylab == 'auto':
            kernel.activate_pylab()
        else:
            kernel.activate_pylab(namespace.pylab)

    # Redirect input streams and set a display hook.
    sys.stdout = OutStream(session, pub_socket, u'stdout')
    sys.stderr = OutStream(session, pub_socket, u'stderr')
    sys.displayhook = DisplayHook(session, pub_socket)

    # Configure this kernel/process to die on parent termination, if necessary.
    if namespace.parent:
        if sys.platform == 'win32':
            poller = ExitPollerWindows(namespace.parent)
        else:
            poller = ExitPollerUnix()
        poller.start()

    # Start the kernel mainloop.
    kernel.start()


def launch_kernel(xrep_port=0, pub_port=0, req_port=0, 
                  pylab=False, independent=False):
    """ Launches a localhost kernel, binding to the specified ports.

    Parameters
    ----------
    xrep_port : int, optional
        The port to use for XREP channel.

    pub_port : int, optional
        The port to use for the SUB channel.

    req_port : int, optional
        The port to use for the REQ (raw input) channel.

    pylab : bool or string, optional (default False)
        If not False, the kernel will be launched with pylab enabled. If a
        string is passed, matplotlib will use the specified backend. Otherwise,
        matplotlib's default backend will be used.

    independent : bool, optional (default False) 
        If set, the kernel process is guaranteed to survive if this process
        dies. If not set, an effort is made to ensure that the kernel is killed
        when this process dies. Note that in this case it is still good practice
        to kill kernels manually before exiting.

    Returns
    -------
    A tuple of form:
        (kernel_process, xrep_port, pub_port, req_port)
    where kernel_process is a Popen object and the ports are integers.
    """
    import socket
    from subprocess import Popen

    # Find open ports as necessary.
    ports = []
    ports_needed = int(xrep_port <= 0) + int(pub_port <= 0) + int(req_port <= 0)
    for i in xrange(ports_needed):
        sock = socket.socket()
        sock.bind(('', 0))
        ports.append(sock)
    for i, sock in enumerate(ports):
        port = sock.getsockname()[1]
        sock.close()
        ports[i] = port
    if xrep_port <= 0:
        xrep_port = ports.pop(0)
    if pub_port <= 0:
        pub_port = ports.pop(0)
    if req_port <= 0:
        req_port = ports.pop(0)

    # Build the kernel launch command.
    command = 'from IPython.zmq.kernel import main; main()'
    arguments = [ sys.executable, '-c', command, '--xrep', str(xrep_port), 
                  '--pub', str(pub_port), '--req', str(req_port) ]
    if pylab:
        arguments.append('--pylab')
        if isinstance(pylab, basestring):
            arguments.append(pylab)

    # Spawn a kernel.
    if independent:
        if sys.platform == 'win32':
            proc = Popen(['start', '/b'] + arguments, shell=True)
        else:
            proc = Popen(arguments, preexec_fn=lambda: os.setsid())
    else:
        if sys.platform == 'win32':
            from _subprocess import DuplicateHandle, GetCurrentProcess, \
                DUPLICATE_SAME_ACCESS
            pid = GetCurrentProcess()
            handle = DuplicateHandle(pid, pid, pid, 0, 
                                     True, # Inheritable by new  processes.
                                     DUPLICATE_SAME_ACCESS)
            proc = Popen(arguments + ['--parent', str(int(handle))])
        else:
            proc = Popen(arguments + ['--parent'])

    return proc, xrep_port, pub_port, req_port
    

if __name__ == '__main__':
    main()
