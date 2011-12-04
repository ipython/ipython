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
from signal import (
        signal, default_int_handler, SIGINT, SIG_IGN
)
# System library imports.
import zmq

# Local imports.
from IPython.core import pylabtools
from IPython.config.configurable import Configurable
from IPython.config.application import boolean_flag, catch_config_error
from IPython.core.application import ProfileDir
from IPython.core.error import StdinNotImplementedError
from IPython.core.shellapp import (
    InteractiveShellApp, shell_flags, shell_aliases
)
from IPython.utils import io
from IPython.utils import py3compat
from IPython.utils.jsonutil import json_clean
from IPython.utils.traitlets import (
    Any, Instance, Float, Dict, CaselessStrEnum
)

from entry_point import base_launch_kernel
from kernelapp import KernelApp, kernel_flags, kernel_aliases
from session import Session, Message
from zmqshell import ZMQInteractiveShell


#-----------------------------------------------------------------------------
# Main kernel class
#-----------------------------------------------------------------------------

class Kernel(Configurable):

    #---------------------------------------------------------------------------
    # Kernel interface
    #---------------------------------------------------------------------------

    # attribute to override with a GUI
    eventloop = Any(None)

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    session = Instance(Session)
    profile_dir = Instance('IPython.core.profiledir.ProfileDir')
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
        self.shell = ZMQInteractiveShell.instance(config=self.config,
            profile_dir = self.profile_dir,
        )
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
        try:
            ident,msg = self.session.recv(self.shell_socket, zmq.NOBLOCK)
        except Exception:
            self.log.warn("Invalid Message:", exc_info=True)
            return
        if msg is None:
            return

        msg_type = msg['header']['msg_type']

        # This assert will raise in versions of zeromq 2.0.7 and lesser.
        # We now require 2.0.8 or above, so we can uncomment for safety.
        # print(ident,msg, file=sys.__stdout__)
        assert ident is not None, "Missing message part."

        # Print some info about this message and leave a '--->' marker, so it's
        # easier to trace visually the message chain when debugging.  Each
        # handler prints its message at the end.
        self.log.debug('\n*** MESSAGE TYPE:'+str(msg_type)+'***')
        self.log.debug('   Content: '+str(msg['content'])+'\n   --->\n   ')

        # Find and call actual handler for message
        handler = self.handlers.get(msg_type, None)
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
        # a KeyboardInterrupt (SIGINT) can occur on any python statement, so
        # let's ignore (SIG_IGN) them until we're in a place to handle them properly
        signal(SIGINT,SIG_IGN)
        poller = zmq.Poller()
        poller.register(self.shell_socket, zmq.POLLIN)
        # loop while self.eventloop has not been overridden
        while self.eventloop is None:
            try:
                # scale by extra factor of 10, because there is no
                # reason for this to be anything less than ~ 0.1s
                # since it is a real poller and will respond
                # to events immediately

                # double nested try/except, to properly catch KeyboardInterrupt
                # due to pyzmq Issue #130
                try:
                    poller.poll(10*1000*self._poll_interval)
                    # restore raising of KeyboardInterrupt
                    signal(SIGINT, default_int_handler)
                    self.do_one_iteration()
                except:
                    raise
                finally:
                    # prevent raising of KeyboardInterrupt
                    signal(SIGINT,SIG_IGN)
            except KeyboardInterrupt:
                # Ctrl-C shouldn't crash the kernel
                io.raw_print("KeyboardInterrupt caught in kernel")
        # stop ignoring sigint, now that we are out of our own loop,
        # we don't want to prevent future code from handling it
        signal(SIGINT, default_int_handler)
        if self.eventloop is not None:
            try:
                self.eventloop(self)
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

        self.session.send(self.iopub_socket, u'pyin', {u'code':code},
                          parent=parent)

    def execute_request(self, ident, parent):

        self.session.send(self.iopub_socket,
                          u'status',
                          {u'execution_state':u'busy'},
                          parent=parent )
        
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
        if content.get('allow_stdin', False):
            raw_input = lambda prompt='': self._raw_input(prompt, ident, parent)
        else:
            raw_input = lambda prompt='' : self._no_raw_input()

        if py3compat.PY3:
            __builtin__.input = raw_input
        else:
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
                shell.run_cell(code, store_history=True)
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
        reply_content = json_clean(reply_content)
        reply_msg = self.session.send(self.shell_socket, u'execute_reply',
                                      reply_content, parent, ident=ident)
        self.log.debug(str(reply_msg))

        if reply_msg['content']['status'] == u'error':
            self._abort_queue()

        self.session.send(self.iopub_socket,
                          u'status',
                          {u'execution_state':u'idle'},
                          parent=parent )

    def complete_request(self, ident, parent):
        txt, matches = self._complete(parent)
        matches = {'matches' : matches,
                   'matched_text' : txt,
                   'status' : 'ok'}
        matches = json_clean(matches)
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
            hist = self.shell.history_manager.search(pattern, raw=raw,
                                                     output=output) 

        else:
            hist = []
        content = {'history' : list(hist)}
        content = json_clean(content)
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
        self._shutdown_message = self.session.msg(u'shutdown_reply',
                                                  parent['content'], parent)
        sys.exit(0)

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _abort_queue(self):
        while True:
            try:
                ident,msg = self.session.recv(self.shell_socket, zmq.NOBLOCK)
            except Exception:
                self.log.warn("Invalid Message:", exc_info=True)
                continue
            if msg is None:
                break
            else:
                assert ident is not None, \
                       "Unexpected missing message part."

            self.log.debug("Aborting:\n"+str(Message(msg)))
            msg_type = msg['header']['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            reply_msg = self.session.send(self.shell_socket, reply_type,
                    {'status' : 'aborted'}, msg, ident=ident)
            self.log.debug(reply_msg)
            # We need to wait a bit for requests to come in. This can probably
            # be set shorter for true asynchronous clients.
            time.sleep(0.1)

    def _no_raw_input(self):
        """Raise StdinNotImplentedError if active frontend doesn't support
        stdin."""
        raise StdinNotImplementedError("raw_input was called, but this "
                                       "frontend does not support stdin.") 
        
    def _raw_input(self, prompt, ident, parent):
        # Flush output before making the request.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the input request.
        content = json_clean(dict(prompt=prompt))
        self.session.send(self.stdin_socket, u'input_request', content, parent,
                          ident=ident)

        # Await a response.
        while True:
            try:
                ident, reply = self.session.recv(self.stdin_socket, 0)
            except Exception:
                self.log.warn("Invalid Message:", exc_info=True)
            else:
                break
        try:
            value = reply['content']['value']
        except:
            self.log.error("Got bad raw_input reply: ")
            self.log.error(str(Message(parent)))
            value = ''
        if value == '\x04':
            # EOF
            raise EOFError
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
    classes = [Kernel, ZMQInteractiveShell, ProfileDir, Session]
    # configurables
    pylab = CaselessStrEnum(['tk', 'qt', 'wx', 'gtk', 'osx', 'inline', 'auto'],
        config=True,
        help="""Pre-load matplotlib and numpy for interactive use,
        selecting a particular matplotlib backend and loop integration.
        """
    )
    
    @catch_config_error
    def initialize(self, argv=None):
        super(IPKernelApp, self).initialize(argv)
        self.init_shell()
        self.init_extensions()
        self.init_code()

    def init_kernel(self):

        kernel = Kernel(config=self.config, session=self.session,
                                shell_socket=self.shell_socket,
                                iopub_socket=self.iopub_socket,
                                stdin_socket=self.stdin_socket,
                                log=self.log,
                                profile_dir=self.profile_dir,
        )
        self.kernel = kernel
        kernel.record_ports(self.ports)
        shell = kernel.shell
        if self.pylab:
            try:
                gui, backend = pylabtools.find_gui_and_backend(self.pylab)
                shell.enable_pylab(gui, import_all=self.pylab_import_all)
            except Exception:
                self.log.error("Pylab initialization failed", exc_info=True)
                # print exception straight to stdout, because normally 
                # _showtraceback associates the reply with an execution, 
                # which means frontends will never draw it, as this exception 
                # is not associated with any execute request.
                
                # replace pyerr-sending traceback with stdout
                _showtraceback = shell._showtraceback
                def print_tb(etype, evalue, stb):
                    print ("Error initializing pylab, pylab mode will not "
                           "be active", file=io.stderr)
                    print (shell.InteractiveTB.stb2text(stb), file=io.stdout)
                shell._showtraceback = print_tb
                
                # send the traceback over stdout
                shell.showtraceback(tb_offset=0)
                
                # restore proper _showtraceback method
                shell._showtraceback = _showtraceback
                

    def init_shell(self):
        self.shell = self.kernel.shell
        self.shell.configurables.append(self)


#-----------------------------------------------------------------------------
# Kernel main and launch functions
#-----------------------------------------------------------------------------

def launch_kernel(*args, **kwargs):
    """Launches a localhost IPython kernel, binding to the specified ports.

    This function simply calls entry_point.base_launch_kernel with the right
    first command to start an ipkernel.  See base_launch_kernel for arguments.

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
