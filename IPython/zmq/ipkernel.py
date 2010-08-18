#!/usr/bin/env python
"""A simple interactive kernel that talks to a frontend over 0MQ.

Things to do:

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
import os
import sys
import time
import traceback

# System library imports.
import zmq

# Local imports.
from IPython.config.configurable import Configurable
from IPython.zmq.zmqshell import ZMQInteractiveShell
from IPython.external.argparse import ArgumentParser
from IPython.utils.traitlets import Instance
from IPython.zmq.session import Session, Message
from completer import KernelCompleter
from iostream import OutStream
from displayhook import DisplayHook
from exitpoller import ExitPollerUnix, ExitPollerWindows

#-----------------------------------------------------------------------------
# Main kernel class
#-----------------------------------------------------------------------------

class Kernel(Configurable):

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    session = Instance('IPython.zmq.session.Session')
    reply_socket = Instance('zmq.Socket')
    pub_socket = Instance('zmq.Socket')
    req_socket = Instance('zmq.Socket')

    def __init__(self, **kwargs):
        super(Kernel, self).__init__(**kwargs)

        # Initialize the InteractiveShell subclass
        self.shell = ZMQInteractiveShell.instance()
        self.shell.displayhook.session = self.session
        self.shell.displayhook.pub_socket = self.pub_socket

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
            # Replace raw_input. Note that is not sufficient to replace 
            # raw_input in the user namespace.
            raw_input = lambda prompt='': self.raw_input(prompt, ident, parent)
            __builtin__.raw_input = raw_input

            # Set the parent message of the display hook.
            self.shell.displayhook.set_parent(parent)

            self.shell.runlines(code)
            # exec comp_code in self.user_ns, self.user_ns
        except:
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
            reply_content = {'status' : 'ok'}
            
        # Flush output before sending the reply.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the reply.
        reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        print>>sys.__stdout__, Message(reply_msg)
        self.reply_socket.send(ident, zmq.SNDMORE)
        self.reply_socket.send_json(reply_msg)
        if reply_msg['content']['status'] == u'error':
            self.abort_queue()

    def raw_input(self, prompt, ident, parent):
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

    def complete_request(self, ident, parent):
        matches = {'matches' : self.complete(parent),
                   'status' : 'ok'}
        completion_msg = self.session.send(self.reply_socket, 'complete_reply',
                                           matches, parent, ident)
        print >> sys.__stdout__, completion_msg

    def complete(self, msg):
        return self.shell.complete(msg.content.line)

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
        symbol = self.shell.user_ns.get(base_symbol_string, None)
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

#-----------------------------------------------------------------------------
# Kernel main and launch functions
#-----------------------------------------------------------------------------

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
    if sys.platform == 'win32':
        parser.add_argument('--parent', type=int, metavar='HANDLE', 
                            default=0, help='kill this process if the process '
                            'with HANDLE dies')
    else:
        parser.add_argument('--parent', action='store_true', 
                            help='kill this process if its parent dies')
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

    # Redirect input streams. This needs to be done before the Kernel is done
    # because currently the Kernel creates a ZMQInteractiveShell, which
    # holds references to sys.stdout and sys.stderr.
    sys.stdout = OutStream(session, pub_socket, u'stdout')
    sys.stderr = OutStream(session, pub_socket, u'stderr')

    # Create the kernel.
    kernel = Kernel(
        session=session, reply_socket=reply_socket,
        pub_socket=pub_socket, req_socket=req_socket
    )

    # Configure this kernel/process to die on parent termination, if necessary.
    if namespace.parent:
        if sys.platform == 'win32':
            poller = ExitPollerWindows(namespace.parent)
        else:
            poller = ExitPollerUnix()
        poller.start()

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
        
    # Spawn a kernel.
    command = 'from IPython.zmq.ipkernel import main; main()'
    arguments = [ sys.executable, '-c', command, '--xrep', str(xrep_port), 
                  '--pub', str(pub_port), '--req', str(req_port) ]
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
