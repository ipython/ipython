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
from IPython.utils import py3compat
from IPython.utils.traitlets import HasTraits, Instance, Dict, Float
from completer import KernelCompleter
from entry_point import base_launch_kernel
from session import Session, Message
from kernelapp import KernelApp

#-----------------------------------------------------------------------------
# Main kernel class
#-----------------------------------------------------------------------------

class Kernel(HasTraits):

    # Private interface

    # Time to sleep after flushing the stdout/err buffers in each execute
    # cycle.  While this introduces a hard limit on the minimal latency of the
    # execute cycle, it helps prevent output synchronization problems for
    # clients.
    # Units are in seconds.  The minimum zmq latency on local host is probably
    # ~150 microseconds, set this to 500us for now.  We may need to increase it
    # a little if it's not enough after more interactive testing.
    _execute_sleep = Float(0.0005, config=True)

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
    log = Instance('logging.Logger')

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
            self.log.debug(str(omsg))
            handler = self.handlers.get(omsg.msg_type, None)
            if handler is None:
                self.log.error("UNKNOWN MESSAGE TYPE: %s"%omsg)
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
            self.log.error("Got bad msg: %s"%Message(parent))
            return
        pyin_msg = self.session.send(self.iopub_socket, u'pyin',{u'code':code}, parent=parent)

        try:
            comp_code = self.compiler(code, '<zmq-kernel>')

            # Replace raw_input. Note that is not sufficient to replace
            # raw_input in the user namespace.
            raw_input = lambda prompt='': self._raw_input(prompt, ident, parent)
            if py3compat.PY3:
                __builtin__.input = raw_input
            else:
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
        # FIXME: on rare occasions, the flush doesn't seem to make it to the
        # clients... This seems to mitigate the problem, but we definitely need
        # to better understand what's going on.
        if self._execute_sleep:
            time.sleep(self._execute_sleep)

        # Send the reply.
        reply_msg = self.session.send(self.shell_socket, u'execute_reply', reply_content, parent, ident=ident)
        self.log.debug(Message(reply_msg))
        if reply_msg['content']['status'] == u'error':
            self._abort_queue()

    def complete_request(self, ident, parent):
        matches = {'matches' : self._complete(parent),
                   'status' : 'ok'}
        completion_msg = self.session.send(self.shell_socket, 'complete_reply',
                                           matches, parent, ident)
        self.log.debug(completion_msg)

    def object_info_request(self, ident, parent):
        context = parent['content']['oname'].split('.')
        object_info = self._object_info(context)
        msg = self.session.send(self.shell_socket, 'object_info_reply',
                                object_info, parent, ident)
        self.log.debug(msg)

    def shutdown_request(self, ident, parent):
        content = dict(parent['content'])
        msg = self.session.send(self.shell_socket, 'shutdown_reply',
                                content, parent, ident)
        msg = self.session.send(self.iopub_socket, 'shutdown_reply',
                                content, parent, ident)
        self.log.debug(msg)
        time.sleep(0.1)
        sys.exit(0)

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _abort_queue(self):
        while True:
            ident,msg = self.session.recv(self.shell_socket, zmq.NOBLOCK)
            if msg is None:
                # msg=None on EAGAIN
                break
            else:
                assert ident is not None, "Missing message part."
            self.log.debug("Aborting: %s"%Message(msg))
            msg_type = msg['header']['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            reply_msg = self.session.send(self.shell_socket, reply_type, {'status':'aborted'}, msg, ident=ident)
            self.log.debug(Message(reply_msg))
            # We need to wait a bit for requests to come in. This can probably
            # be set shorter for true asynchronous clients.
            time.sleep(0.1)

    def _raw_input(self, prompt, ident, parent):
        # Flush output before making the request.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the input request.
        content = dict(prompt=prompt)
        msg = self.session.send(self.stdin_socket, u'input_request', content, parent, ident=ident)

        # Await a response.
        ident,reply = self.session.recv(self.stdin_socket, 0)
        try:
            value = reply['content']['value']
        except:
            self.log.error("Got bad raw_input reply: %s"%Message(parent))
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
    app = KernelApp.instance()
    app.initialize()
    app.start()

if __name__ == '__main__':
    main()
