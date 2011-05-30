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
import sys
import time
import traceback

# System library imports.
import zmq

# Local imports.
from IPython.utils.traitlets import HasTraits, Instance, Dict
from completer import KernelCompleter
from entry_point import base_launch_kernel
from session import Session, Message
from kernelapp import KernelApp

#-----------------------------------------------------------------------------
# Main kernel class
#-----------------------------------------------------------------------------

class Kernel(HasTraits):

    # Private interface

    # This is a dict of port number that the kernel is listening on. It is set
    # by record_ports and used by connect_request.
    _recorded_ports = Dict()

    #---------------------------------------------------------------------------
    # Kernel interface
    #---------------------------------------------------------------------------

    session = Instance(Session)
    shell_socket = Instance('zmq.Socket')
    iopub_socket = Instance('zmq.Socket')
    stdin_socket = Instance('zmq.Socket')

    def __init__(self, **kwargs):
        super(Kernel, self).__init__(**kwargs)
        self.user_ns = {}
        self.history = []
        self.compiler = CommandCompiler()
        self.completer = KernelCompleter(self.user_ns)

        # Build dict of handlers for message types
        msg_types = [ 'execute_request', 'complete_request', 
                      'object_info_request', 'shutdown_request' ]
        self.handlers = {}
        for msg_type in msg_types:
            self.handlers[msg_type] = getattr(self, msg_type)

    def start(self):
        """ Start the kernel main loop.
        """
        while True:
            ident,msg = self.session.recv(self.shell_socket,0)
            assert ident is not None, "Missing message part."
            omsg = Message(msg)
            print>>sys.__stdout__
            print>>sys.__stdout__, omsg
            handler = self.handlers.get(omsg.msg_type, None)
            if handler is None:
                print >> sys.__stderr__, "UNKNOWN MESSAGE TYPE:", omsg
            else:
                handler(ident, omsg)

    def record_ports(self, ports):
        """Record the ports that this kernel is using.

        The creator of the Kernel instance must call this methods if they
        want the :meth:`connect_request` method to return the port numbers.
        """
        self._recorded_ports = ports

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
        pyin_msg = self.session.send(self.iopub_socket, u'pyin',{u'code':code}, parent=parent)

        try:
            comp_code = self.compiler(code, '<zmq-kernel>')

            # Replace raw_input. Note that is not sufficient to replace 
            # raw_input in the user namespace.
            raw_input = lambda prompt='': self._raw_input(prompt, ident, parent)
            __builtin__.raw_input = raw_input

            # Set the parent message of the display hook and out streams.
            sys.displayhook.set_parent(parent)
            sys.stdout.set_parent(parent)
            sys.stderr.set_parent(parent)

            exec comp_code in self.user_ns, self.user_ns
        except:
            etype, evalue, tb = sys.exc_info()
            tb = traceback.format_exception(etype, evalue, tb)
            exc_content = {
                u'status' : u'error',
                u'traceback' : tb,
                u'ename' : unicode(etype.__name__),
                u'evalue' : unicode(evalue)
            }
            exc_msg = self.session.send(self.iopub_socket, u'pyerr', exc_content, parent)
            reply_content = exc_content
        else:
            reply_content = { 'status' : 'ok', 'payload' : {} }
            
        # Flush output before sending the reply.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the reply.
        reply_msg = self.session.send(self.shell_socket, u'execute_reply', reply_content, parent, ident=ident)
        print>>sys.__stdout__, Message(reply_msg)
        if reply_msg['content']['status'] == u'error':
            self._abort_queue()

    def complete_request(self, ident, parent):
        matches = {'matches' : self._complete(parent),
                   'status' : 'ok'}
        completion_msg = self.session.send(self.shell_socket, 'complete_reply',
                                           matches, parent, ident)
        print >> sys.__stdout__, completion_msg

    def object_info_request(self, ident, parent):
        context = parent['content']['oname'].split('.')
        object_info = self._object_info(context)
        msg = self.session.send(self.shell_socket, 'object_info_reply',
                                object_info, parent, ident)
        print >> sys.__stdout__, msg

    def shutdown_request(self, ident, parent):
        content = dict(parent['content'])
        msg = self.session.send(self.shell_socket, 'shutdown_reply',
                                content, parent, ident)
        msg = self.session.send(self.iopub_socket, 'shutdown_reply',
                                content, parent, ident)
        print >> sys.__stdout__, msg
        time.sleep(0.1)
        sys.exit(0)

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _abort_queue(self):
        while True:
            ident,msg = self.session.recv(self.reply_socket, zmq.NOBLOCK)
            if msg is None:
                break
            else:
                assert ident is not None, "Unexpected missing message part."
            print>>sys.__stdout__, "Aborting:"
            print>>sys.__stdout__, Message(msg)
            msg_type = msg['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            reply_msg = self.session.send(self.shell_socket, reply_type, {'status':'aborted'}, msg, ident=ident)
            print>>sys.__stdout__, Message(reply_msg)
            # We need to wait a bit for requests to come in. This can probably
            # be set shorter for true asynchronous clients.
            time.sleep(0.1)

    def _raw_input(self, prompt, ident, parent):
        # Flush output before making the request.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the input request.
        content = dict(prompt=prompt)
        msg = self.session.send(self.stdin_socket, u'input_request', content, parent)

        # Await a response.
        ident,reply = self.session.recv(self.stdin_socket, 0)
        try:
            value = reply['content']['value']
        except:
            print>>sys.__stderr__, "Got bad raw_input reply: "
            print>>sys.__stderr__, Message(parent)
            value = ''
        return value

    def _complete(self, msg):
        return self.completer.complete(msg.content.line, msg.content.text)

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

def launch_kernel(*args, **kwargs):
    """ Launches a simple Python kernel, binding to the specified ports.
    
    This function simply calls entry_point.base_launch_kernel with the right first
    command to start a pykernel.  See base_launch_kernel for arguments.

    Returns
    -------
    A tuple of form:
        (kernel_process, xrep_port, pub_port, req_port, hb_port)
    where kernel_process is a Popen object and the ports are integers.
    """
    return base_launch_kernel('from IPython.zmq.pykernel import main; main()',
                                *args, **kwargs)

def main():
    """Run a PyKernel as an application"""
    app = KernelApp()
    app.initialize()
    app.start()

if __name__ == '__main__':
    main()
