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
from __future__ import print_function

# Standard library imports.
import __builtin__
import sys
import time
import traceback

# System library imports.
import zmq

# Local imports.
from IPython.config.configurable import Configurable
from IPython.utils import io
from IPython.lib import pylabtools
from IPython.utils.traitlets import Instance
from entry_point import base_launch_kernel, make_argument_parser, make_kernel, \
    start_kernel
from iostream import OutStream
from session import Session, Message
from zmqshell import ZMQInteractiveShell


#-----------------------------------------------------------------------------
# Main kernel class
#-----------------------------------------------------------------------------

class Kernel(Configurable):

    #---------------------------------------------------------------------------
    # Kernel interface
    #---------------------------------------------------------------------------

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    session = Instance(Session)
    reply_socket = Instance('zmq.Socket')
    pub_socket = Instance('zmq.Socket')
    req_socket = Instance('zmq.Socket')

    def __init__(self, **kwargs):
        super(Kernel, self).__init__(**kwargs)

        # Initialize the InteractiveShell subclass
        self.shell = ZMQInteractiveShell.instance()
        self.shell.displayhook.session = self.session
        self.shell.displayhook.pub_socket = self.pub_socket

        # TMP - hack while developing
        self.shell._reply_content = None

        # Build dict of handlers for message types
        msg_types = [ 'execute_request', 'complete_request', 
                      'object_info_request', 'history_request' ]
        self.handlers = {}
        for msg_type in msg_types:
            self.handlers[msg_type] = getattr(self, msg_type)

    def do_one_iteration(self):
        try:
            ident = self.reply_socket.recv(zmq.NOBLOCK)
        except zmq.ZMQError, e:
            if e.errno == zmq.EAGAIN:
                return
            else:
                raise
        # FIXME: Bug in pyzmq/zmq?
        # assert self.reply_socket.rcvmore(), "Missing message part."
        msg = self.reply_socket.recv_json()
        
        # Print some info about this message and leave a '--->' marker, so it's
        # easier to trace visually the message chain when debugging.  Each
        # handler prints its message at the end.
        # Eventually we'll move these from stdout to a logger.
        io.raw_print('\n*** MESSAGE TYPE:', msg['msg_type'], '***')
        io.raw_print('   Content: ', msg['content'],
                     '\n   --->\n   ', sep='', end='')

        # Find and call actual handler for message
        handler = self.handlers.get(msg['msg_type'], None)
        if handler is None:
            io.raw_print_err("UNKNOWN MESSAGE TYPE:", msg)
        else:
            handler(ident, msg)

    def start(self):
        """ Start the kernel main loop.
        """
        while True:
            time.sleep(0.05)
            self.do_one_iteration()

    #---------------------------------------------------------------------------
    # Kernel request handlers
    #---------------------------------------------------------------------------

    def _publish_pyin(self, code, parent):
        """Publish the code request on the pyin stream."""

        pyin_msg = self.session.msg(u'pyin',{u'code':code}, parent=parent)
        self.pub_socket.send_json(pyin_msg)

    def execute_request(self, ident, parent):
        try:
            content = parent[u'content']
            code = content[u'code']
            silent = content[u'silent'] 
        except:
            io.raw_print_err("Got bad msg: ")
            io.raw_print_err(Message(parent))
            return

        shell = self.shell # we'll need this a lot here

        # Replace raw_input. Note that is not sufficient to replace 
        # raw_input in the user namespace.
        raw_input = lambda prompt='': self._raw_input(prompt, ident, parent)
        __builtin__.raw_input = raw_input

        # Set the parent message of the display hook and out streams.
        shell.displayhook.set_parent(parent)
        sys.stdout.set_parent(parent)
        sys.stderr.set_parent(parent)

        # Re-broadcast our input for the benefit of listening clients, and
        # start computing output
        if not silent:
            self._publish_pyin(code, parent)

        reply_content = {}
        try:
            if silent:
                # runcode uses 'exec' mode, so no displayhook will fire, and it
                # doesn't call logging or history manipulations.  Print
                # statements in that code will obviously still execute.
                shell.runcode(code)
            else:
                # FIXME: runlines calls the exception handler itself.
                shell._reply_content = None
                shell.runlines(code)
        except:
            status = u'error'
            # FIXME: this code right now isn't being used yet by default,
            # because the runlines() call above directly fires off exception
            # reporting.  This code, therefore, is only active in the scenario
            # where runlines itself has an unhandled exception.  We need to
            # uniformize this, for all exception construction to come from a
            # single location in the codbase.
            etype, evalue, tb = sys.exc_info()
            tb_list = traceback.format_exception(etype, evalue, tb)
            reply_content.update(shell._showtraceback(etype, evalue, tb_list))
        else:
            status = u'ok'
            reply_content[u'payload'] = shell.payload_manager.read_payload()
            # Be agressive about clearing the payload because we don't want
            # it to sit in memory until the next execute_request comes in.
            shell.payload_manager.clear_payload()

        reply_content[u'status'] = status
        # Compute the execution counter so clients can display prompts
        reply_content['execution_count'] = shell.displayhook.prompt_count

        # FIXME - fish exception info out of shell, possibly left there by
        # runlines.  We'll need to clean up this logic later.
        if shell._reply_content is not None:
            reply_content.update(shell._reply_content)

        # At this point, we can tell whether the main code execution succeeded
        # or not.  If it did, we proceed to evaluate user_variables/expressions
        if reply_content['status'] == 'ok':
            reply_content[u'user_variables'] = \
                         shell.get_user_variables(content[u'user_variables'])
            reply_content[u'user_expressions'] = \
                         shell.eval_expressions(content[u'user_expressions'])
        else:
            # If there was an error, don't even try to compute variables or
            # expressions
            reply_content[u'user_variables'] = {}
            reply_content[u'user_expressions'] = {}
            
        # Send the reply.
        reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        io.raw_print(reply_msg)
        self.reply_socket.send(ident, zmq.SNDMORE)
        self.reply_socket.send_json(reply_msg)
        if reply_msg['content']['status'] == u'error':
            self._abort_queue()

    def complete_request(self, ident, parent):
        txt, matches = self._complete(parent)
        matches = {'matches' : matches,
                   'matched_text' : txt,
                   'status' : 'ok'}
        completion_msg = self.session.send(self.reply_socket, 'complete_reply',
                                           matches, parent, ident)
        io.raw_print(completion_msg)

    def object_info_request(self, ident, parent):
        context = parent['content']['oname'].split('.')
        object_info = self._object_info(context)
        msg = self.session.send(self.reply_socket, 'object_info_reply',
                                object_info, parent, ident)
        io.raw_print(msg)

    def history_request(self, ident, parent):
        output = parent['content']['output']
        index = parent['content']['index']
        raw = parent['content']['raw']
        hist = self.shell.get_history(index=index, raw=raw, output=output)
        content = {'history' : hist}
        msg = self.session.send(self.reply_socket, 'history_reply',
                                content, parent, ident)
        io.raw_print(msg)
        
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
                assert self.reply_socket.rcvmore(), \
                       "Unexpected missing message part."
                msg = self.reply_socket.recv_json()
            io.raw_print("Aborting:\n", Message(msg))
            msg_type = msg['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            reply_msg = self.session.msg(reply_type, {'status' : 'aborted'}, msg)
            io.raw_print(reply_msg)
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
            io.raw_print_err("Got bad raw_input reply: ")
            io.raw_print_err(Message(parent))
            value = ''
        return value
    
    def _complete(self, msg):
        c = msg['content']
        try:
            cpos = int(c['cursor_pos'])
        except:
            # If we don't get something that we can convert to an integer, at
            # least attempt the completion guessing the cursor is at the end of
            # the text, if there's any, and otherwise of the line
            cpos = len(c['text'])
            if cpos==0:
                cpos = len(c['line'])
        return self.shell.complete(c['text'], c['line'], cpos)

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


class QtKernel(Kernel):
    """A Kernel subclass with Qt support."""

    def start(self):
        """Start a kernel with QtPy4 event loop integration."""

        from PyQt4 import QtGui, QtCore
        from IPython.lib.guisupport import (
            get_app_qt4, start_event_loop_qt4
        )
        self.app = get_app_qt4([" "])
        self.app.setQuitOnLastWindowClosed(False)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.do_one_iteration)
        self.timer.start(50)
        start_event_loop_qt4(self.app)


class WxKernel(Kernel):
    """A Kernel subclass with Wx support."""

    def start(self):
        """Start a kernel with wx event loop support."""

        import wx
        from IPython.lib.guisupport import start_event_loop_wx
        doi = self.do_one_iteration

        # We have to put the wx.Timer in a wx.Frame for it to fire properly.
        # We make the Frame hidden when we create it in the main app below.
        class TimerFrame(wx.Frame):
            def __init__(self, func):
                wx.Frame.__init__(self, None, -1)
                self.timer = wx.Timer(self)
                self.timer.Start(50)
                self.Bind(wx.EVT_TIMER, self.on_timer)
                self.func = func
            def on_timer(self, event):
                self.func()

        # We need a custom wx.App to create our Frame subclass that has the
        # wx.Timer to drive the ZMQ event loop.
        class IPWxApp(wx.App):
            def OnInit(self):
                self.frame = TimerFrame(doi)
                self.frame.Show(False)
                return True

        # The redirect=False here makes sure that wx doesn't replace
        # sys.stdout/stderr with its own classes.
        self.app = IPWxApp(redirect=False)
        start_event_loop_wx(self.app)


class TkKernel(Kernel):
    """A Kernel subclass with Tk support."""

    def start(self):
        """Start a Tk enabled event loop."""

        import Tkinter
        doi = self.do_one_iteration

        # For Tkinter, we create a Tk object and call its withdraw method.
        class Timer(object):
            def __init__(self, func):
                self.app = Tkinter.Tk()
                self.app.withdraw()
                self.func = func
            def on_timer(self):
                self.func()
                self.app.after(50, self.on_timer)
            def start(self):
                self.on_timer()  # Call it once to get things going.
                self.app.mainloop()

        self.timer = Timer(doi)
        self.timer.start()

#-----------------------------------------------------------------------------
# Kernel main and launch functions
#-----------------------------------------------------------------------------

def launch_kernel(xrep_port=0, pub_port=0, req_port=0, hb_port=0,
                  independent=False, pylab=False):
    """ Launches a localhost kernel, binding to the specified ports.

    Parameters
    ----------
    xrep_port : int, optional
        The port to use for XREP channel.

    pub_port : int, optional
        The port to use for the SUB channel.

    req_port : int, optional
        The port to use for the REQ (raw input) channel.

    hb_port : int, optional
        The port to use for the hearbeat REP channel.

    independent : bool, optional (default False) 
        If set, the kernel process is guaranteed to survive if this process
        dies. If not set, an effort is made to ensure that the kernel is killed
        when this process dies. Note that in this case it is still good practice
        to kill kernels manually before exiting.

    pylab : bool or string, optional (default False)
        If not False, the kernel will be launched with pylab enabled. If a
        string is passed, matplotlib will use the specified backend. Otherwise,
        matplotlib's default backend will be used.

    Returns
    -------
    A tuple of form:
        (kernel_process, xrep_port, pub_port, req_port)
    where kernel_process is a Popen object and the ports are integers.
    """
    extra_arguments = []
    if pylab:
        extra_arguments.append('--pylab')
        if isinstance(pylab, basestring):
            extra_arguments.append(pylab)
    return base_launch_kernel('from IPython.zmq.ipkernel import main; main()',
                              xrep_port, pub_port, req_port, hb_port, 
                              independent, extra_arguments)


def main():
    """ The IPython kernel main entry point.
    """
    parser = make_argument_parser()
    parser.add_argument('--pylab', type=str, metavar='GUI', nargs='?', 
                        const='auto', help = \
"Pre-load matplotlib and numpy for interactive use. If GUI is not \
given, the GUI backend is matplotlib's, otherwise use one of: \
['tk', 'gtk', 'qt', 'wx', 'payload-svg'].")
    namespace = parser.parse_args()

    kernel_class = Kernel

    _kernel_classes = {
        'qt' : QtKernel,
        'qt4' : QtKernel,
        'payload-svg': Kernel,
        'wx' : WxKernel,
        'tk' : TkKernel
    }
    if namespace.pylab:
        if namespace.pylab == 'auto':
            gui, backend = pylabtools.find_gui_and_backend()
        else:
            gui, backend = pylabtools.find_gui_and_backend(namespace.pylab)
        kernel_class = _kernel_classes.get(gui)
        if kernel_class is None:
            raise ValueError('GUI is not supported: %r' % gui)
        pylabtools.activate_matplotlib(backend)

    kernel = make_kernel(namespace, kernel_class, OutStream)

    if namespace.pylab:
        pylabtools.import_pylab(kernel.shell.user_ns)

    start_kernel(namespace, kernel)


if __name__ == '__main__':
    main()
