# -*- coding: utf-8 -*-
"""Frontend of ipython working with python-zmq

Ipython's frontend, is a ipython interface that send request to kernel and proccess the kernel's outputs.

For more details, see the ipython-zmq design
"""
#-----------------------------------------------------------------------------
# Copyright (C) 2011 The IPython Development Team
#
# Distributed under the terms of the BSD License. The full license is in
# the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

import bdb
import sys

from Queue import Empty

from IPython.core.alias import AliasManager, AliasError
from IPython.utils.warn import warn, error, fatal
from IPython.utils import io

from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell
from IPython.frontend.zmqterminal.completer import ZMQCompleter


class ZMQTerminalInteractiveShell(TerminalInteractiveShell):
    """A subclass of TerminalInteractiveShell that """
    
    def __init__(self, *args, **kwargs):
        self.km = kwargs.pop('kernel_manager')
        self.session_id = self.km.session.session
        super(ZMQTerminalInteractiveShell, self).__init__(*args, **kwargs)
        
    def init_completer(self):
        """Initialize the completion machinery.

        This creates completion machinery that can be used by client code,
        either interactively in-process (typically triggered by the readline
        library), programatically (such as in test suites) or out-of-prcess
        (typically over the network by remote frontends).
        """
        from IPython.core.completerlib import (module_completer,
                                               magic_run_completer, cd_completer)
        
        self.Completer = ZMQCompleter(self, self.km)
        

        self.set_hook('complete_command', module_completer, str_key = 'import')
        self.set_hook('complete_command', module_completer, str_key = 'from')
        self.set_hook('complete_command', magic_run_completer, str_key = '%run')
        self.set_hook('complete_command', cd_completer, str_key = '%cd')

        # Only configure readline if we truly are using readline.  IPython can
        # do tab-completion over the network, in GUIs, etc, where readline
        # itself may be absent
        if self.has_readline:
            self.set_readline_completer()
    
    def run_cell(self, cell, store_history=True):
        """Run a complete IPython cell.
        
        Parameters
        ----------
        cell : str
          The code (including IPython code such as %magic functions) to run.
        store_history : bool
          If True, the raw and translated cell will be stored in IPython's
          history. For user code calling back into IPython's machinery, this
          should be set to False.
        """
        if (not cell) or cell.isspace():
            return

        # shell_channel.execute takes 'hidden', which is the inverse of store_hist
        msg_id = self.km.shell_channel.execute(cell, not store_history)
        while not self.km.shell_channel.msg_ready():
            try:
                self.handle_stdin_request(timeout=0.05)
            except Empty:
                pass
        self.handle_execute_reply(msg_id)

    #-----------------
    # message handlers
    #-----------------

    def handle_execute_reply(self, msg_id):
        msg = self.km.shell_channel.get_msg()
        if msg["parent_header"]["msg_id"] == msg_id:
            if msg["content"]["status"] == 'ok' :
                self.handle_iopub()
               
            elif msg["content"]["status"] == 'error':
                for frame in msg["content"]["traceback"]:
                    print(frame, file=io.stderr)
            
            self.execution_count = int(msg["content"]["execution_count"] + 1)


    def handle_iopub(self):
        """ Method to procces subscribe channel's messages

           This method reads a message and processes the content in different
           outputs like stdout, stderr, pyout and status

           Arguments:
           sub_msg:  message receive from kernel in the sub socket channel
                     capture by kernel manager.
        """
        while self.km.sub_channel.msg_ready():
            sub_msg = self.km.sub_channel.get_msg()
            msg_type = sub_msg['header']['msg_type']
            if self.session_id == sub_msg['parent_header']['session']:
                if msg_type == 'status' :
                    if sub_msg["content"]["execution_state"] == "busy" :
                        pass

                elif msg_type == 'stream' :
                    if sub_msg["content"]["name"] == "stdout":
                        print(sub_msg["content"]["data"], file=io.stdout, end="")
                        io.stdout.flush()
                    elif sub_msg["content"]["name"] == "stderr" :
                        print(sub_msg["content"]["data"], file=io.stderr, end="")
                        io.stderr.flush()

                elif msg_type == 'pyout':
                    self.execution_count = int(sub_msg["content"]["execution_count"])
                    format_dict = sub_msg["content"]["data"]
                    # taken from DisplayHook.__call__:
                    hook = self.displayhook
                    hook.start_displayhook()
                    hook.write_output_prompt()
                    hook.write_format_data(format_dict)
                    hook.log_output(format_dict)
                    hook.finish_displayhook()

    def handle_stdin_request(self, timeout=0.1):
        """ Method to capture raw_input
        """
        msg_rep = self.km.stdin_channel.get_msg(timeout=timeout)
        if self.session_id == msg_rep["parent_header"]["session"] :
            raw_data = raw_input(msg_rep["content"]["prompt"])
            self.km.stdin_channel.input(raw_data)

    def mainloop(self, display_banner=False):
        while True:
            try:
                self.interact(display_banner=display_banner)
                #self.interact_with_readline()                
                # XXX for testing of a readline-decoupled repl loop, call
                # interact_with_readline above
                break
            except KeyboardInterrupt:
                # this should not be necessary, but KeyboardInterrupt
                # handling seems rather unpredictable...
                self.write("\nKeyboardInterrupt in interact()\n")
    
    def interact(self, display_banner=None):
        """Closely emulate the interactive Python console."""

        # batch run -> do not interact
        if self.exit_now:
            return

        if display_banner is None:
            display_banner = self.display_banner
        
        if isinstance(display_banner, basestring):
            self.show_banner(display_banner)
        elif display_banner:
            self.show_banner()

        more = False
        
        if self.has_readline:
            self.readline_startup_hook(self.pre_readline)
        # exit_now is set by a call to %Exit or %Quit, through the
        # ask_exit callback.

        while not self.exit_now:
            if not self.km.is_alive:
                ans = self.raw_input("kernel died, restart ([y]/n)?")
                if not ans.lower().startswith('n'):
                    self.km.restart_kernel(True)
                else:
                    self.exit_now=True
                continue
            self.hooks.pre_prompt_hook()
            if more:
                try:
                    prompt = self.hooks.generate_prompt(True)
                except:
                    self.showtraceback()
                if self.autoindent:
                    self.rl_do_indent = True
                    
            else:
                try:
                    prompt = self.hooks.generate_prompt(False)
                except:
                    self.showtraceback()
            try:
                line = self.raw_input(prompt)
                if self.exit_now:
                    # quick exit on sys.std[in|out] close
                    break
                if self.autoindent:
                    self.rl_do_indent = False
                    
            except KeyboardInterrupt:
                #double-guard against keyboardinterrupts during kbdint handling
                try:
                    self.write('\nKeyboardInterrupt\n')
                    self.input_splitter.reset()
                    more = False
                except KeyboardInterrupt:
                    pass
            except EOFError:
                if self.autoindent:
                    self.rl_do_indent = False
                    if self.has_readline:
                        self.readline_startup_hook(None)
                self.write('\n')
                self.exit()
            except bdb.BdbQuit:
                warn('The Python debugger has exited with a BdbQuit exception.\n'
                     'Because of how pdb handles the stack, it is impossible\n'
                     'for IPython to properly format this particular exception.\n'
                     'IPython will resume normal operation.')
            except:
                # exceptions here are VERY RARE, but they can be triggered
                # asynchronously by signal handlers, for example.
                self.showtraceback()
            else:
                self.input_splitter.push(line)
                more = self.input_splitter.push_accepts_more()
                if (self.SyntaxTB.last_syntax_error and
                    self.autoedit_syntax):
                    self.edit_syntax_error()
                if not more:
                    source_raw = self.input_splitter.source_reset()
                    self.run_cell(source_raw)
                

        # Turn off the exit flag, so the mainloop can be restarted if desired
        self.exit_now = False
