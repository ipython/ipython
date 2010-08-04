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

# Standard library imports.
import __builtin__
import os
import sys
import time
import traceback
from code import CommandCompiler

# System library imports.
import zmq

# Local imports.
from IPython.external.argparse import ArgumentParser
from session import Session, Message, extract_header
from completer import KernelCompleter


class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    def __init__(self, session, pub_socket, name, max_buffer=200):
        self.session = session
        self.pub_socket = pub_socket
        self.name = name
        self._buffer = []
        self._buffer_len = 0
        self.max_buffer = max_buffer
        self.parent_header = {}

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    def flush(self):
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        else:
            if self._buffer:
                data = ''.join(self._buffer)
                content = {u'name':self.name, u'data':data}
                msg = self.session.msg(u'stream', content=content,
                                       parent=self.parent_header)
                print>>sys.__stdout__, Message(msg)
                self.pub_socket.send_json(msg)
                self._buffer_len = 0
                self._buffer = []

    def isattr(self):
        return False

    def next(self):
        raise IOError('Read not supported on a write only stream.')

    def read(self, size=None):
        raise IOError('Read not supported on a write only stream.')

    readline=read

    def write(self, s):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            self._buffer.append(s)
            self._buffer_len += len(s)
            self._maybe_send()

    def _maybe_send(self):
        if '\n' in self._buffer[-1]:
            self.flush()
        if self._buffer_len > self.max_buffer:
            self.flush()

    def writelines(self, sequence):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            for s in sequence:
                self.write(s)


class DisplayHook(object):

    def __init__(self, session, pub_socket):
        self.session = session
        self.pub_socket = pub_socket
        self.parent_header = {}

    def __call__(self, obj):
        if obj is None:
            return

        __builtin__._ = obj
        msg = self.session.msg(u'pyout', {u'data':repr(obj)},
                               parent=self.parent_header)
        self.pub_socket.send_json(msg)

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)


class RawInput(object):

    def __init__(self, session, socket):
        self.session = session
        self.socket = socket

    def __call__(self, prompt=None):
        msg = self.session.msg(u'raw_input')
        self.socket.send_json(msg)
        while True:
            try:
                reply = self.socket.recv_json(zmq.NOBLOCK)
            except zmq.ZMQError, e:
                if e.errno == zmq.EAGAIN:
                    pass
                else:
                    raise
            else:
                break
        return reply[u'content'][u'data']


class Kernel(object):

    def __init__(self, session, reply_socket, pub_socket):
        self.session = session
        self.reply_socket = reply_socket
        self.pub_socket = pub_socket
        self.user_ns = {}
        self.history = []
        self.compiler = CommandCompiler()
        self.completer = KernelCompleter(self.user_ns)
        self.poll_ppid = False
        
        # Build dict of handlers for message types
        msg_types = [ 'execute_request', 'complete_request', 
                      'object_info_request' ]
        self.handlers = {}
        for msg_type in msg_types:
            self.handlers[msg_type] = getattr(self, msg_type)

    def abort_queue(self):
        while True:
            try:
                ident = self.reply_socket.recv(zmq.NOBLOCK)
            except zmq.ZMQError, e:
                if e.errno == zmq.EAGAIN:
                    break
            else:
                assert self.reply_socket.rcvmore(), "Unexpected missing message part."
                msg = self.reply_socket.recv_json()
            print>>sys.__stdout__, "Aborting:"
            print>>sys.__stdout__, Message(msg)
            msg_type = msg['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            reply_msg = self.session.msg(reply_type, {'status' : 'aborted'}, msg)
            print>>sys.__stdout__, Message(reply_msg)
            self.reply_socket.send(ident,zmq.SNDMORE)
            self.reply_socket.send_json(reply_msg)
            # We need to wait a bit for requests to come in. This can probably
            # be set shorter for true asynchronous clients.
            time.sleep(0.1)

    def execute_request(self, ident, parent):
        try:
            code = parent[u'content'][u'code']
        except:
            print>>sys.__stderr__, "Got bad msg: "
            print>>sys.__stderr__, Message(parent)
            return
        pyin_msg = self.session.msg(u'pyin',{u'code':code}, parent=parent)
        self.pub_socket.send_json(pyin_msg)
        try:
            comp_code = self.compiler(code, '<zmq-kernel>')
            sys.displayhook.set_parent(parent)
            exec comp_code in self.user_ns, self.user_ns
        except:
            result = u'error'
            etype, evalue, tb = sys.exc_info()
            tb = traceback.format_exception(etype, evalue, tb)
            exc_content = {
                u'status' : u'error',
                u'traceback' : tb,
                u'etype' : unicode(etype),
                u'evalue' : unicode(evalue)
            }
            exc_msg = self.session.msg(u'pyerr', exc_content, parent)
            self.pub_socket.send_json(exc_msg)
            reply_content = exc_content
        else:
            reply_content = {'status' : 'ok'}
        reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        print>>sys.__stdout__, Message(reply_msg)
        self.reply_socket.send(ident, zmq.SNDMORE)
        self.reply_socket.send_json(reply_msg)
        if reply_msg['content']['status'] == u'error':
            self.abort_queue()

    def complete_request(self, ident, parent):
        matches = {'matches' : self.complete(parent),
                   'status' : 'ok'}
        completion_msg = self.session.send(self.reply_socket, 'complete_reply',
                                           matches, parent, ident)
        print >> sys.__stdout__, completion_msg

    def complete(self, msg):
        return self.completer.complete(msg.content.line, msg.content.text)

    def object_info_request(self, ident, parent):
        context = parent['content']['oname'].split('.')
        object_info = self.object_info(context)
        msg = self.session.send(self.reply_socket, 'object_info_reply',
                                object_info, parent, ident)
        print >> sys.__stdout__, msg

    def object_info(self, context):
        symbol, leftover = self.symbol_from_context(context)
        if symbol is not None and not leftover:
            doc = getattr(symbol, '__doc__', '')
        else:
            doc = ''
        object_info = dict(docstring = doc)
        return object_info

    def symbol_from_context(self, context):
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

    def start(self):
        while True:
            if self.poll_ppid and os.getppid() == 1:
                print>>sys.__stderr__, "KILLED KERNEL. No parent process."
                os._exit(1)

            ident = self.reply_socket.recv()
            assert self.reply_socket.rcvmore(), "Unexpected missing message part."
            msg = self.reply_socket.recv_json()
            omsg = Message(msg)
            print>>sys.__stdout__
            print>>sys.__stdout__, omsg
            handler = self.handlers.get(omsg.msg_type, None)
            if handler is None:
                print >> sys.__stderr__, "UNKNOWN MESSAGE TYPE:", omsg
            else:
                handler(ident, omsg)


def bind_port(socket, ip, port):
    """ Binds the specified ZMQ socket. If the port is less than zero, a random
    port is chosen. Returns the port that was bound.
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
    parser.add_argument('--require-parent', action='store_true', 
                        help='ensure that this process dies with its parent')
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

    # Redirect input streams and set a display hook.
    sys.stdout = OutStream(session, pub_socket, u'stdout')
    sys.stderr = OutStream(session, pub_socket, u'stderr')
    sys.displayhook = DisplayHook(session, pub_socket)

    # Create the kernel.
    kernel = Kernel(session, reply_socket, pub_socket)

    # Configure this kernel/process to die on parent termination, if necessary.
    if namespace.require_parent:
        if sys.platform == 'linux2':
            import ctypes, ctypes.util, signal
            PR_SET_PDEATHSIG = 1
            libc = ctypes.CDLL(ctypes.util.find_library('c'))
            libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL)

        elif sys.platform != 'win32':
            kernel.poll_ppid = True

    # Start the kernel mainloop.
    kernel.start()


def launch_kernel(xrep_port=0, pub_port=0, req_port=0, independent=False):
    """ Launches a localhost kernel, binding to the specified ports.

    Parameters
    ----------
    xrep_port : int, optional
        The port to use for XREP channel.

    pub_port : int, optional
        The port to use for the SUB channel.

    req_port : int, optional
        The port to use for the REQ (raw input) channel.

    independent : bool, optional (default False) 
        If set, the kernel process is guaranteed to survive if this process
        dies. If not set, an effort is made to ensure that the kernel is killed
        when this process dies. Note that in this case it is still good practice
        to attempt to kill kernels manually before exiting.

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
        
    # Spawn a kernel.
    command = 'from IPython.zmq.kernel import main; main()'
    arguments = [ sys.executable, '-c', command, '--xrep', str(xrep_port), 
                  '--pub', str(pub_port), '--req', str(req_port) ]

    if independent:
        if sys.platform == 'win32':
            proc = Popen(['start', '/b'] + arguments, shell=True)
        else:
            proc = Popen(arguments, preexec_fn=lambda: os.setsid())

    else:
        proc = Popen(arguments + ['--require-parent'])

    return proc, xrep_port, pub_port, req_port
    

if __name__ == '__main__':
    main()
