#!/usr/bin/env python
"""A simple interactive frontend that talks to a kernel over 0MQ.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# stdlib
import cPickle as pickle
import code
import readline
import sys
import time
import uuid

# our own
import zmq
import session
import completer
from IPython.utils.localinterfaces import LOCALHOST
from IPython.kernel.zmq.session import Message

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class Console(code.InteractiveConsole):

    def __init__(self, locals=None, filename="<console>",
                 session = session,
                 request_socket=None,
                 sub_socket=None):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.session = session
        self.request_socket = request_socket
        self.sub_socket = sub_socket
        self.backgrounded = 0
        self.messages = {}

        # Set tab completion
        self.completer = completer.ClientCompleter(self, session, request_socket)
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set show-all-if-ambiguous on')
        readline.set_completer(self.completer.complete)

        # Set system prompts
        sys.ps1 = 'Py>>> '
        sys.ps2 = '  ... '
        sys.ps3 = 'Out : '
        # Build dict of handlers for message types
        self.handlers = {}
        for msg_type in ['pyin', 'pyout', 'pyerr', 'stream']:
            self.handlers[msg_type] = getattr(self, 'handle_%s' % msg_type)

    def handle_pyin(self, omsg):
        if omsg.parent_header.session == self.session.session:
            return
        c = omsg.content.code.rstrip()
        if c:
            print('[IN from %s]' % omsg.parent_header.username)
            print(c)

    def handle_pyout(self, omsg):
        #print omsg # dbg
        if omsg.parent_header.session == self.session.session:
            print("%s%s" % (sys.ps3, omsg.content.data))
        else:
            print('[Out from %s]' % omsg.parent_header.username)
            print(omsg.content.data)

    def print_pyerr(self, err):
        print(err.etype,':', err.evalue, file=sys.stderr)
        print(''.join(err.traceback), file=sys.stderr)

    def handle_pyerr(self, omsg):
        if omsg.parent_header.session == self.session.session:
            return
        print('[ERR from %s]' % omsg.parent_header.username, file=sys.stderr)
        self.print_pyerr(omsg.content)

    def handle_stream(self, omsg):
        if omsg.content.name == 'stdout':
            outstream = sys.stdout
        else:
            outstream = sys.stderr
            print('*ERR*', end=' ', file=outstream)
        print(omsg.content.data, end=' ', file=outstream)

    def handle_output(self, omsg):
        handler = self.handlers.get(omsg.msg_type, None)
        if handler is not None:
            handler(omsg)

    def recv_output(self):
        while True:
            ident,msg = self.session.recv(self.sub_socket)
            if msg is None:
                break
            self.handle_output(Message(msg))

    def handle_reply(self, rep):
        # Handle any side effects on output channels
        self.recv_output()
        # Now, dispatch on the possible reply types we must handle
        if rep is None:
            return
        if rep.content.status == 'error':
            self.print_pyerr(rep.content)
        elif rep.content.status == 'aborted':
            print("ERROR: ABORTED", file=sys.stderr)
            ab = self.messages[rep.parent_header.msg_id].content
            if 'code' in ab:
                print(ab.code, file=sys.stderr)
            else:
                print(ab, file=sys.stderr)

    def recv_reply(self):
        ident,rep = self.session.recv(self.request_socket)
        mrep = Message(rep)
        self.handle_reply(mrep)
        return mrep

    def runcode(self, code):
        # We can't pickle code objects, so fetch the actual source
        src = '\n'.join(self.buffer)

        # for non-background inputs, if we do have previoiusly backgrounded
        # jobs, check to see if they've produced results
        if not src.endswith(';'):
            while self.backgrounded > 0:
                #print 'checking background'
                rep = self.recv_reply()
                if rep:
                    self.backgrounded -= 1
                time.sleep(0.05)

        # Send code execution message to kernel
        omsg = self.session.send(self.request_socket,
                                 'execute_request', dict(code=src))
        self.messages[omsg.header.msg_id] = omsg

        # Fake asynchronicity by letting the user put ';' at the end of the line
        if src.endswith(';'):
            self.backgrounded += 1
            return

        # For foreground jobs, wait for reply
        while True:
            rep = self.recv_reply()
            if rep is not None:
                break
            self.recv_output()
            time.sleep(0.05)
        else:
            # We exited without hearing back from the kernel!
            print('ERROR!!! kernel never got back to us!!!', file=sys.stderr)


class InteractiveClient(object):
    def __init__(self, session, request_socket, sub_socket):
        self.session = session
        self.request_socket = request_socket
        self.sub_socket = sub_socket
        self.console = Console(None, '<zmq-console>',
                               session, request_socket, sub_socket)

    def interact(self):
        self.console.interact()


def main():
    # Defaults
    #ip = '192.168.2.109'
    ip = LOCALHOST
    #ip = '99.146.222.252'
    port_base = 5575
    connection = ('tcp://%s' % ip) + ':%i'
    req_conn = connection % port_base
    sub_conn = connection % (port_base+1)

    # Create initial sockets
    c = zmq.Context()
    request_socket = c.socket(zmq.DEALER)
    request_socket.connect(req_conn)

    sub_socket = c.socket(zmq.SUB)
    sub_socket.connect(sub_conn)
    sub_socket.setsockopt(zmq.SUBSCRIBE, '')

    # Make session and user-facing client
    sess = session.Session()
    client = InteractiveClient(sess, request_socket, sub_socket)
    client.interact()


if __name__ == '__main__':
    main()
