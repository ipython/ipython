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
import atexit
import sys
import time
import traceback
import logging
# System library imports.
import zmq

# Local imports.
from IPython.config.configurable import Configurable
from IPython.config.application import boolean_flag
from IPython.core.newapplication import ProfileDir
from IPython.core.shellapp import (
    InteractiveShellApp, shell_flags, shell_aliases
)
from IPython.utils import io
from IPython.utils.jsonutil import json_clean
from IPython.lib import pylabtools
from IPython.utils.traitlets import (
    List, Instance, Float, Dict, Bool, Int, Unicode, CaselessStrEnum
)

from entry_point import base_launch_kernel
from kernelapp import KernelApp, kernel_flags, kernel_aliases
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
    shell_socket = Instance('zmq.Socket')
    iopub_socket = Instance('zmq.Socket')
    stdin_socket = Instance('zmq.Socket')
    log = Instance(logging.Logger)

    # Private interface

    # Time to sleep after flushing the stdout/err buffers in each execute
    # cycle.  While this introduces a hard limit on the minimal latency of the
    # execute cycle, it helps prevent output synchronization problems for
    # clients.
    # Units are in seconds.  The minimum zmq latency on local host is probably
    # ~150 microseconds, set this to 500us for now.  We may need to increase it
    # a little if it's not enough after more interactive testing.
    _execute_sleep = Float(0.0005, config=True)

    # Frequency of the kernel's event loop.
    # Units are in seconds, kernel subclasses for GUI toolkits may need to
    # adapt to milliseconds.
    _poll_interval = Float(0.05, config=True)

    # If the shutdown was requested over the network, we leave here the
    # necessary reply message so it can be sent by our registered atexit
    # handler.  This ensures that the reply is only sent to clients truly at
    # the end of our shutdown process (which happens after the underlying
    # IPython shell's own shutdown).
    _shutdown_message = None

    # This is a dict of port number that the kernel is listening on. It is set
    # by record_ports and used by connect_request.
    _recorded_ports = Dict()



    def __init__(self, **kwargs):
        super(Kernel, self).__init__(**kwargs)

        # Before we even start up the shell, register *first* our exit handlers
        # so they come before the shell's
        atexit.register(self._at_shutdown)

        # Initialize the InteractiveShell subclass
        self.shell = ZMQInteractiveShell.instance(config=self.config)
        self.shell.displayhook.session = self.session
        self.shell.displayhook.pub_socket = self.iopub_socket
        self.shell.display_pub.session = self.session
        self.shell.display_pub.pub_socket = self.iopub_socket

        # TMP - hack while developing
        self.shell._reply_content = None

        # Build dict of handlers for message types
        msg_types = [ 'execute_request', 'complete_request', 
                      'object_info_request', 'history_request',
                      'connect_request', 'shutdown_request']
        self.handlers = {}
        for msg_type in msg_types:
            self.handlers[msg_type] = getattr(self, msg_type)

    def do_one_iteration(self):
        """Do one iteration of the kernel's evaluation loop.
        """
        ident,msg = self.session.recv(self.shell_socket, zmq.NOBLOCK)
        if msg is None:
            return
        
        # This assert will raise in versions of zeromq 2.0.7 and lesser.
        # We now require 2.0.8 or above, so we can uncomment for safety.
        # print(ident,msg, file=sys.__stdout__)
        assert ident is not None, "Missing message part."
        
        # Print some info about this message and leave a '--->' marker, so it's
        # easier to trace visually the message chain when debugging.  Each
        # handler prints its message at the end.
        self.log.debug('\n*** MESSAGE TYPE:'+str(msg['msg_type'])+'***')
        self.log.debug('   Content: '+str(msg['content'])+'\n   --->\n   ')

        # Find and call actual handler for message
        handler = self.handlers.get(msg['msg_type'], None)
        if handler is None:
            self.log.error("UNKNOWN MESSAGE TYPE:" +str(msg))
        else:
            handler(ident, msg)
            
        # Check whether we should exit, in case the incoming message set the
        # exit flag on
        if self.shell.exit_now:
            self.log.debug('\nExiting IPython kernel...')
            # We do a normal, clean exit, which allows any actions registered
            # via atexit (such as history saving) to take place.
            sys.exit(0)


    def start(self):
        """ Start the kernel main loop.
        """
        poller = zmq.Poller()
        poller.register(self.shell_socket, zmq.POLLIN)
        while True:
            try:
                # scale by extra factor of 10, because there is no
                # reason for this to be anything less than ~ 0.1s
                # since it is a real poller and will respond
                # to events immediately
                poller.poll(10*1000*self._poll_interval)
                self.do_one_iteration()
            except KeyboardInterrupt:
                # Ctrl-C shouldn't crash the kernel
                io.raw_print("KeyboardInterrupt caught in kernel")

    def record_ports(self, ports):
        """Record the ports that this kernel is using.

        The creator of the Kernel instance must call this methods if they
        want the :meth:`connect_request` method to return the port numbers.
        """
        self._recorded_ports = ports

    #---------------------------------------------------------------------------
    # Kernel request handlers
    #---------------------------------------------------------------------------

    def _publish_pyin(self, code, parent):
        """Publish the code request on the pyin stream."""

        pyin_msg = self.session.send(self.iopub_socket, u'pyin',{u'code':code}, parent=parent)

    def execute_request(self, ident, parent):
        
        status_msg = self.session.send(self.iopub_socket,
            u'status',
            {u'execution_state':u'busy'},
            parent=parent
        )
        
        try:
            content = parent[u'content']
            code = content[u'code']
            silent = content[u'silent'] 
        except:
            self.log.error("Got bad msg: ")
            self.log.error(str(Message(parent)))
            return

        shell = self.shell # we'll need this a lot here

        # Replace raw_input. Note that is not sufficient to replace 
        # raw_input in the user namespace.
        raw_input = lambda prompt='': self._raw_input(prompt, ident, parent)
        __builtin__.raw_input = raw_input

        # Set the parent message of the display hook and out streams.
        shell.displayhook.set_parent(parent)
        shell.display_pub.set_parent(parent)
        sys.stdout.set_parent(parent)
        sys.stderr.set_parent(parent)

        # Re-broadcast our input for the benefit of listening clients, and
        # start computing output
        if not silent:
            self._publish_pyin(code, parent)

        reply_content = {}
        try:
            if silent:
                # run_code uses 'exec' mode, so no displayhook will fire, and it
                # doesn't call logging or history manipulations.  Print
                # statements in that code will obviously still execute.
                shell.run_code(code)
            else:
                # FIXME: the shell calls the exception handler itself.
                shell.run_cell(code)
        except:
            status = u'error'
            # FIXME: this code right now isn't being used yet by default,
            # because the run_cell() call above directly fires off exception
            # reporting.  This code, therefore, is only active in the scenario
            # where runlines itself has an unhandled exception.  We need to
            # uniformize this, for all exception construction to come from a
            # single location in the codbase.
            etype, evalue, tb = sys.exc_info()
            tb_list = traceback.format_exception(etype, evalue, tb)
            reply_content.update(shell._showtraceback(etype, evalue, tb_list))
        else:
            status = u'ok'

        reply_content[u'status'] = status
        
        # Return the execution counter so clients can display prompts
        reply_content['execution_count'] = shell.execution_count -1

        # FIXME - fish exception info out of shell, possibly left there by
        # runlines.  We'll need to clean up this logic later.
        if shell._reply_content is not None:
            reply_content.update(shell._reply_content)
            # reset after use
            shell._reply_content = None

        # At this point, we can tell whether the main code execution succeeded
        # or not.  If it did, we proceed to evaluate user_variables/expressions
        if reply_content['status'] == 'ok':
            reply_content[u'user_variables'] = \
                         shell.user_variables(content[u'user_variables'])
            reply_content[u'user_expressions'] = \
                         shell.user_expressions(content[u'user_expressions'])
        else:
            # If there was an error, don't even try to compute variables or
            # expressions
            reply_content[u'user_variables'] = {}
            reply_content[u'user_expressions'] = {}

        # Payloads should be retrieved regardless of outcome, so we can both
        # recover partial output (that could have been generated early in a
        # block, before an error) and clear the payload system always.
        reply_content[u'payload'] = shell.payload_manager.read_payload()
        # Be agressive about clearing the payload because we don't want
        # it to sit in memory until the next execute_request comes in.
        shell.payload_manager.clear_payload()

        # Flush output before sending the reply.
        sys.stdout.flush()
        sys.stderr.flush()
        # FIXME: on rare occasions, the flush doesn't seem to make it to the
        # clients... This seems to mitigate the problem, but we definitely need
        # to better understand what's going on.
        if self._execute_sleep:
            time.sleep(self._execute_sleep)
        
        # Send the reply.
        reply_msg = self.session.send(self.shell_socket, u'execute_reply',
                                      reply_content, parent, ident=ident)
        self.log.debug(str(reply_msg))

        if reply_msg['content']['status'] == u'error':
            self._abort_queue()

        status_msg = self.session.send(self.iopub_socket,
            u'status',
            {u'execution_state':u'idle'},
            parent=parent
        )

    def complete_request(self, ident, parent):
        txt, matches = self._complete(parent)
        matches = {'matches' : matches,
                   'matched_text' : txt,
                   'status' : 'ok'}
        completion_msg = self.session.send(self.shell_socket, 'complete_reply',
                                           matches, parent, ident)
        self.log.debug(str(completion_msg))

    def object_info_request(self, ident, parent):
        object_info = self.shell.object_inspect(parent['content']['oname'])
        # Before we send this object over, we scrub it for JSON usage
        oinfo = json_clean(object_info)
        msg = self.session.send(self.shell_socket, 'object_info_reply',
                                oinfo, parent, ident)
        self.log.debug(msg)

    def history_request(self, ident, parent):
        # We need to pull these out, as passing **kwargs doesn't work with
        # unicode keys before Python 2.6.5.
        hist_access_type = parent['content']['hist_access_type']
        raw = parent['content']['raw']
        output = parent['content']['output']
        if hist_access_type == 'tail':
            n = parent['content']['n']
            hist = self.shell.history_manager.get_tail(n, raw=raw, output=output,
                                                            include_latest=True)
        
        elif hist_access_type == 'range':
            session = parent['content']['session']
            start = parent['content']['start']
            stop = parent['content']['stop']
            hist = self.shell.history_manager.get_range(session, start, stop,
                                                        raw=raw, output=output)
        
        elif hist_access_type == 'search':
            pattern = parent['content']['pattern']
            hist = self.shell.history_manager.search(pattern, raw=raw, output=output)
        
        else:
            hist = []
        content = {'history' : list(hist)}
        msg = self.session.send(self.shell_socket, 'history_reply',
                                content, parent, ident)
        self.log.debug(str(msg))

    def connect_request(self, ident, parent):
        if self._recorded_ports is not None:
            content = self._recorded_ports.copy()
        else:
            content = {}
        msg = self.session.send(self.shell_socket, 'connect_reply',
                                content, parent, ident)
        self.log.debug(msg)

    def shutdown_request(self, ident, parent):
        self.shell.exit_now = True
        self._shutdown_message = self.session.msg(u'shutdown_reply', parent['content'], parent)
        sys.exit(0)

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _abort_queue(self):
        while True:
            ident,msg = self.session.recv(self.shell_socket, zmq.NOBLOCK)
            if msg is None:
                break
            else:
                assert ident is not None, \
                       "Unexpected missing message part."

            self.log.debug("Aborting:\n"+str(Message(msg)))
            msg_type = msg['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            reply_msg = self.session.send(self.shell_socket, reply_type,
                    {'status' : 'aborted'}, msg, ident=ident)
            self.log.debug(reply_msg)
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
        ident, reply = self.session.recv(self.stdin_socket, 0)
        try:
            value = reply['content']['value']
        except:
            self.log.error("Got bad raw_input reply: ")
            self.log.error(str(Message(parent)))
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

    def _at_shutdown(self):
        """Actions taken at shutdown by the kernel, called by python's atexit.
        """
        # io.rprint("Kernel at_shutdown") # dbg
        if self._shutdown_message is not None:
            self.session.send(self.shell_socket, self._shutdown_message)
            self.session.send(self.iopub_socket, self._shutdown_message)
            self.log.debug(str(self._shutdown_message))
            # A very short sleep to give zmq time to flush its message buffers
            # before Python truly shuts down.
            time.sleep(0.01)


class QtKernel(Kernel):
    """A Kernel subclass with Qt support."""

    def start(self):
        """Start a kernel with QtPy4 event loop integration."""

        from PyQt4 import QtCore
        from IPython.lib.guisupport import get_app_qt4, start_event_loop_qt4

        self.app = get_app_qt4([" "])
        self.app.setQuitOnLastWindowClosed(False)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.do_one_iteration)
        # Units for the timer are in milliseconds
        self.timer.start(1000*self._poll_interval)
        start_event_loop_qt4(self.app)


class WxKernel(Kernel):
    """A Kernel subclass with Wx support."""

    def start(self):
        """Start a kernel with wx event loop support."""

        import wx
        from IPython.lib.guisupport import start_event_loop_wx

        doi = self.do_one_iteration
         # Wx uses milliseconds
        poll_interval = int(1000*self._poll_interval)

        # We have to put the wx.Timer in a wx.Frame for it to fire properly.
        # We make the Frame hidden when we create it in the main app below.
        class TimerFrame(wx.Frame):
            def __init__(self, func):
                wx.Frame.__init__(self, None, -1)
                self.timer = wx.Timer(self)
                # Units for the timer are in milliseconds
                self.timer.Start(poll_interval)
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
        # Tk uses milliseconds
        poll_interval = int(1000*self._poll_interval)
        # For Tkinter, we create a Tk object and call its withdraw method.
        class Timer(object):
            def __init__(self, func):
                self.app = Tkinter.Tk()
                self.app.withdraw()
                self.func = func
                
            def on_timer(self):
                self.func()
                self.app.after(poll_interval, self.on_timer)
                
            def start(self):
                self.on_timer()  # Call it once to get things going.
                self.app.mainloop()

        self.timer = Timer(doi)
        self.timer.start()


class GTKKernel(Kernel):
    """A Kernel subclass with GTK support."""
    
    def start(self):
        """Start the kernel, coordinating with the GTK event loop"""
        from .gui.gtkembed import GTKEmbed
        
        gtk_kernel = GTKEmbed(self)
        gtk_kernel.start()


#-----------------------------------------------------------------------------
# Aliases and Flags for the IPKernelApp
#-----------------------------------------------------------------------------

flags = dict(kernel_flags)
flags.update(shell_flags)

addflag = lambda *args: flags.update(boolean_flag(*args))

flags['pylab'] = (
    {'IPKernelApp' : {'pylab' : 'auto'}},
    """Pre-load matplotlib and numpy for interactive use with
    the default matplotlib backend."""
)

aliases = dict(kernel_aliases)
aliases.update(shell_aliases)

# it's possible we don't want short aliases for *all* of these:
aliases.update(dict(
    pylab='IPKernelApp.pylab',
))

#-----------------------------------------------------------------------------
# The IPKernelApp class
#-----------------------------------------------------------------------------

class IPKernelApp(KernelApp, InteractiveShellApp):
    name = 'ipkernel'

    aliases = Dict(aliases)
    flags = Dict(flags)
    classes = [Kernel, ZMQInteractiveShell, ProfileDir]
    # configurables
    pylab = CaselessStrEnum(['tk', 'qt', 'wx', 'gtk', 'osx', 'inline', 'auto'],
        config=True,
        help="""Pre-load matplotlib and numpy for interactive use,
        selecting a particular matplotlib backend and loop integration.
        """
    )
    def initialize(self, argv=None):
        super(IPKernelApp, self).initialize(argv)
        self.init_shell()
        self.init_extensions()
        self.init_code()

    def init_kernel(self):
        kernel_factory = Kernel

        kernel_map = {
            'qt' : QtKernel,
            'qt4': QtKernel,
            'inline': Kernel,
            'osx': TkKernel,
            'wx' : WxKernel,
            'tk' : TkKernel,
            'gtk': GTKKernel,
        }

        if self.pylab:
            key = None if self.pylab == 'auto' else self.pylab
            gui, backend = pylabtools.find_gui_and_backend(key)
            kernel_factory = kernel_map.get(gui)
            if kernel_factory is None:
                raise ValueError('GUI is not supported: %r' % gui)
            pylabtools.activate_matplotlib(backend)

        kernel = kernel_factory(config=self.config, session=self.session,
                                shell_socket=self.shell_socket,
                                iopub_socket=self.iopub_socket,
                                stdin_socket=self.stdin_socket,
                                log=self.log
        )
        self.kernel = kernel
        kernel.record_ports(self.ports)

        if self.pylab:
            pylabtools.import_pylab(kernel.shell.user_ns, backend,
                                    shell=kernel.shell)
    
    def init_shell(self):
        self.shell = self.kernel.shell


#-----------------------------------------------------------------------------
# Kernel main and launch functions
#-----------------------------------------------------------------------------

def launch_kernel(*args, **kwargs):
    """Launches a localhost IPython kernel, binding to the specified ports.

    This function simply calls entry_point.base_launch_kernel with the right first
    command to start an ipkernel.  See base_launch_kernel for arguments.

    Returns
    -------
    A tuple of form:
        (kernel_process, shell_port, iopub_port, stdin_port, hb_port)
    where kernel_process is a Popen object and the ports are integers.
    """
    return base_launch_kernel('from IPython.zmq.ipkernel import main; main()',
                              *args, **kwargs)


def main():
    """Run an IPKernel as an application"""
    app = IPKernelApp.instance()
    app.initialize()
    app.start()


if __name__ == '__main__':
    main()
