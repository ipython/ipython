# -*- coding: utf-8 -*-
"""terminal client to the IPython kernel

"""
#-----------------------------------------------------------------------------
# Copyright (C) 2013 The IPython Development Team
#
# Distributed under the terms of the BSD License. The full license is in
# the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

import bdb
import signal
import os
import sys
import time
import subprocess
from io import BytesIO
import base64

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

from IPython.core import page
from IPython.utils.warn import warn, error
from IPython.utils import io
from IPython.utils.py3compat import string_types, input
from IPython.utils.traitlets import List, Enum, Any, Instance, Unicode, Float
from IPython.utils.tempdir import NamedFileInTemporaryDirectory

from IPython.terminal.interactiveshell import TerminalInteractiveShell
from IPython.terminal.console.completer import ZMQCompleter


class ZMQTerminalInteractiveShell(TerminalInteractiveShell):
    """A subclass of TerminalInteractiveShell that uses the 0MQ kernel"""
    _executing = False
    _execution_state = Unicode('')
    _pending_clearoutput = False
    kernel_timeout = Float(60, config=True,
        help="""Timeout for giving up on a kernel (in seconds).
        
        On first connect and restart, the console tests whether the
        kernel is running and responsive by sending kernel_info_requests.
        This sets the timeout in seconds for how long the kernel can take
        before being presumed dead.
        """
    )

    image_handler = Enum(('PIL', 'stream', 'tempfile', 'callable'),
                         config=True, help=
        """
        Handler for image type output.  This is useful, for example,
        when connecting to the kernel in which pylab inline backend is
        activated.  There are four handlers defined.  'PIL': Use
        Python Imaging Library to popup image; 'stream': Use an
        external program to show the image.  Image will be fed into
        the STDIN of the program.  You will need to configure
        `stream_image_handler`; 'tempfile': Use an external program to
        show the image.  Image will be saved in a temporally file and
        the program is called with the temporally file.  You will need
        to configure `tempfile_image_handler`; 'callable': You can set
        any Python callable which is called with the image data.  You
        will need to configure `callable_image_handler`.
        """
    )

    stream_image_handler = List(config=True, help=
        """
        Command to invoke an image viewer program when you are using
        'stream' image handler.  This option is a list of string where
        the first element is the command itself and reminders are the
        options for the command.  Raw image data is given as STDIN to
        the program.
        """
    )

    tempfile_image_handler = List(config=True, help=
        """
        Command to invoke an image viewer program when you are using
        'tempfile' image handler.  This option is a list of string
        where the first element is the command itself and reminders
        are the options for the command.  You can use {file} and
        {format} in the string to represent the location of the
        generated image file and image format.
        """
    )

    callable_image_handler = Any(config=True, help=
        """
        Callable object called via 'callable' image handler with one
        argument, `data`, which is `msg["content"]["data"]` where
        `msg` is the message from iopub channel.  For exmaple, you can
        find base64 encoded PNG data as `data['image/png']`.
        """
    )

    mime_preference = List(
        default_value=['image/png', 'image/jpeg', 'image/svg+xml'],
        config=True, allow_none=False, help=
        """
        Preferred object representation MIME type in order.  First
        matched MIME type will be used.
        """
    )

    manager = Instance('IPython.kernel.KernelManager')
    client = Instance('IPython.kernel.KernelClient')
    def _client_changed(self, name, old, new):
        self.session_id = new.session.session
    session_id = Unicode()

    def init_completer(self):
        """Initialize the completion machinery.

        This creates completion machinery that can be used by client code,
        either interactively in-process (typically triggered by the readline
        library), programmatically (such as in test suites) or out-of-process
        (typically over the network by remote frontends).
        """
        from IPython.core.completerlib import (module_completer,
                                               magic_run_completer, cd_completer)
        
        self.Completer = ZMQCompleter(self, self.client, config=self.config)
        

        self.set_hook('complete_command', module_completer, str_key = 'import')
        self.set_hook('complete_command', module_completer, str_key = 'from')
        self.set_hook('complete_command', magic_run_completer, str_key = '%run')
        self.set_hook('complete_command', cd_completer, str_key = '%cd')

        # Only configure readline if we truly are using readline.  IPython can
        # do tab-completion over the network, in GUIs, etc, where readline
        # itself may be absent
        if self.has_readline:
            self.set_readline_completer()
    
    def ask_exit(self):
        super(ZMQTerminalInteractiveShell, self).ask_exit()
        if self.exit_now and self.manager:
            self.client.shutdown()
    
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
            # pressing enter flushes any pending display
            self.handle_iopub()
            return

        if cell.strip() == 'exit':
            # explicitly handle 'exit' command
            return self.ask_exit()

        # flush stale replies, which could have been ignored, due to missed heartbeats
        while self.client.shell_channel.msg_ready():
            self.client.shell_channel.get_msg()
        # shell_channel.execute takes 'hidden', which is the inverse of store_hist
        msg_id = self.client.shell_channel.execute(cell, not store_history)
        
        # first thing is wait for any side effects (output, stdin, etc.)
        self._executing = True
        self._execution_state = "busy"
        while self._execution_state != 'idle' and self.client.is_alive():
            try:
                self.handle_stdin_request(msg_id, timeout=0.05)
            except Empty:
                # display intermediate print statements, etc.
                self.handle_iopub(msg_id)
        
        # after all of that is done, wait for the execute reply
        while self.client.is_alive():
            try:
                self.handle_execute_reply(msg_id, timeout=0.05)
            except Empty:
                pass
            else:
                break
        self._executing = False

    #-----------------
    # message handlers
    #-----------------

    def handle_execute_reply(self, msg_id, timeout=None):
        msg = self.client.shell_channel.get_msg(block=False, timeout=timeout)
        if msg["parent_header"].get("msg_id", None) == msg_id:
            
            self.handle_iopub(msg_id)
            
            content = msg["content"]
            status = content['status']
            
            if status == 'aborted':
                self.write('Aborted\n')
                return
            elif status == 'ok':
                # print execution payloads as well:
                for item in content["payload"]:
                    text = item.get('text', None)
                    if text:
                        page.page(text)
               
            elif status == 'error':
                for frame in content["traceback"]:
                    print(frame, file=io.stderr)
            
            self.execution_count = int(content["execution_count"] + 1)


    def handle_iopub(self, msg_id=''):
        """Process messages on the IOPub channel

           This method consumes and processes messages on the IOPub channel,
           such as stdout, stderr, pyout and status.
           
           It only displays output that is caused by this session.
        """
        while self.client.iopub_channel.msg_ready():
            sub_msg = self.client.iopub_channel.get_msg()
            msg_type = sub_msg['header']['msg_type']
            parent = sub_msg["parent_header"]
            
            if parent.get("session", self.session_id) == self.session_id:
                if msg_type == 'status':
                    self._execution_state = sub_msg["content"]["execution_state"]
                elif msg_type == 'stream':
                    if sub_msg["content"]["name"] == "stdout":
                        if self._pending_clearoutput:
                            print("\r", file=io.stdout, end="")
                            self._pending_clearoutput = False
                        print(sub_msg["content"]["data"], file=io.stdout, end="")
                        io.stdout.flush()
                    elif sub_msg["content"]["name"] == "stderr" :
                        if self._pending_clearoutput:
                            print("\r", file=io.stderr, end="")
                            self._pending_clearoutput = False
                        print(sub_msg["content"]["data"], file=io.stderr, end="")
                        io.stderr.flush()

                elif msg_type == 'pyout':
                    if self._pending_clearoutput:
                        print("\r", file=io.stdout, end="")
                        self._pending_clearoutput = False
                    self.execution_count = int(sub_msg["content"]["execution_count"])
                    format_dict = sub_msg["content"]["data"]
                    self.handle_rich_data(format_dict)
                    # taken from DisplayHook.__call__:
                    hook = self.displayhook
                    hook.start_displayhook()
                    hook.write_output_prompt()
                    hook.write_format_data(format_dict)
                    hook.log_output(format_dict)
                    hook.finish_displayhook()

                elif msg_type == 'display_data':
                    data = sub_msg["content"]["data"]
                    handled = self.handle_rich_data(data)
                    if not handled:
                        # if it was an image, we handled it by now
                        if 'text/plain' in data:
                            print(data['text/plain'])

                elif msg_type == 'clear_output':
                    if sub_msg["content"]["wait"]:
                        self._pending_clearoutput = True
                    else:
                        print("\r", file=io.stdout, end="")

    _imagemime = {
        'image/png': 'png',
        'image/jpeg': 'jpeg',
        'image/svg+xml': 'svg',
    }

    def handle_rich_data(self, data):
        for mime in self.mime_preference:
            if mime in data and mime in self._imagemime:
                self.handle_image(data, mime)
                return True

    def handle_image(self, data, mime):
        handler = getattr(
            self, 'handle_image_{0}'.format(self.image_handler), None)
        if handler:
            handler(data, mime)

    def handle_image_PIL(self, data, mime):
        if mime not in ('image/png', 'image/jpeg'):
            return
        import PIL.Image
        raw = base64.decodestring(data[mime].encode('ascii'))
        img = PIL.Image.open(BytesIO(raw))
        img.show()

    def handle_image_stream(self, data, mime):
        raw = base64.decodestring(data[mime].encode('ascii'))
        imageformat = self._imagemime[mime]
        fmt = dict(format=imageformat)
        args = [s.format(**fmt) for s in self.stream_image_handler]
        with open(os.devnull, 'w') as devnull:
            proc = subprocess.Popen(
                args, stdin=subprocess.PIPE,
                stdout=devnull, stderr=devnull)
            proc.communicate(raw)

    def handle_image_tempfile(self, data, mime):
        raw = base64.decodestring(data[mime].encode('ascii'))
        imageformat = self._imagemime[mime]
        filename = 'tmp.{0}'.format(imageformat)
        with NamedFileInTemporaryDirectory(filename) as f, \
                    open(os.devnull, 'w') as devnull:
            f.write(raw)
            f.flush()
            fmt = dict(file=f.name, format=imageformat)
            args = [s.format(**fmt) for s in self.tempfile_image_handler]
            subprocess.call(args, stdout=devnull, stderr=devnull)

    def handle_image_callable(self, data, mime):
        self.callable_image_handler(data)

    def handle_stdin_request(self, msg_id, timeout=0.1):
        """ Method to capture raw_input
        """
        msg_rep = self.client.stdin_channel.get_msg(timeout=timeout)
        # in case any iopub came while we were waiting:
        self.handle_iopub(msg_id)
        if msg_id == msg_rep["parent_header"].get("msg_id"):
            # wrap SIGINT handler
            real_handler = signal.getsignal(signal.SIGINT)
            def double_int(sig,frame):
                # call real handler (forwards sigint to kernel),
                # then raise local interrupt, stopping local raw_input
                real_handler(sig,frame)
                raise KeyboardInterrupt
            signal.signal(signal.SIGINT, double_int)
            
            try:
                raw_data = input(msg_rep["content"]["prompt"])
            except EOFError:
                # turn EOFError into EOF character
                raw_data = '\x04'
            except KeyboardInterrupt:
                sys.stdout.write('\n')
                return
            finally:
                # restore SIGINT handler
                signal.signal(signal.SIGINT, real_handler)
            
            # only send stdin reply if there *was not* another request
            # or execution finished while we were reading.
            if not (self.client.stdin_channel.msg_ready() or self.client.shell_channel.msg_ready()):
                self.client.stdin_channel.input(raw_data)

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
    
    def wait_for_kernel(self, timeout=None):
        """method to wait for a kernel to be ready"""
        tic = time.time()
        self.client.hb_channel.unpause()
        while True:
            msg_id = self.client.kernel_info()
            reply = None
            while True:
                try:
                    reply = self.client.get_shell_msg(timeout=1)
                except Empty:
                    break
                else:
                    if reply['parent_header'].get('msg_id') == msg_id:
                        return True
            if timeout is not None \
                and (time.time() - tic) > timeout \
                and not self.client.hb_channel.is_beating():
                # heart failed
                return False
        return True
    
    def interact(self, display_banner=None):
        """Closely emulate the interactive Python console."""

        # batch run -> do not interact
        if self.exit_now:
            return

        if display_banner is None:
            display_banner = self.display_banner
        
        if isinstance(display_banner, string_types):
            self.show_banner(display_banner)
        elif display_banner:
            self.show_banner()

        more = False
        
        # run a non-empty no-op, so that we don't get a prompt until
        # we know the kernel is ready. This keeps the connection
        # message above the first prompt.
        if not self.wait_for_kernel(self.kernel_timeout):
            error("Kernel did not respond\n")
            return
        
        if self.has_readline:
            self.readline_startup_hook(self.pre_readline)
            hlen_b4_cell = self.readline.get_current_history_length()
        else:
            hlen_b4_cell = 0
        # exit_now is set by a call to %Exit or %Quit, through the
        # ask_exit callback.

        while not self.exit_now:
            if not self.client.is_alive():
                # kernel died, prompt for action or exit

                action = "restart" if self.manager else "wait for restart"
                ans = self.ask_yes_no("kernel died, %s ([y]/n)?" % action, default='y')
                if ans:
                    if self.manager:
                        self.manager.restart_kernel(True)
                    self.wait_for_kernel(self.kernel_timeout)
                else:
                    self.exit_now = True
                continue
            try:
                # protect prompt block from KeyboardInterrupt
                # when sitting on ctrl-C
                self.hooks.pre_prompt_hook()
                if more:
                    try:
                        prompt = self.prompt_manager.render('in2')
                    except Exception:
                        self.showtraceback()
                    if self.autoindent:
                        self.rl_do_indent = True
                    
                else:
                    try:
                        prompt = self.separate_in + self.prompt_manager.render('in')
                    except Exception:
                        self.showtraceback()
                
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
                    source_raw = self.input_splitter.raw_reset()
                    hlen_b4_cell = self._replace_rlhist_multiline(source_raw, hlen_b4_cell)
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
                try:
                    self.input_splitter.push(line)
                    more = self.input_splitter.push_accepts_more()
                except SyntaxError:
                    # Run the code directly - run_cell takes care of displaying
                    # the exception.
                    more = False
                if (self.SyntaxTB.last_syntax_error and
                    self.autoedit_syntax):
                    self.edit_syntax_error()
                if not more:
                    source_raw = self.input_splitter.raw_reset()
                    hlen_b4_cell = self._replace_rlhist_multiline(source_raw, hlen_b4_cell)
                    self.run_cell(source_raw)
                

        # Turn off the exit flag, so the mainloop can be restarted if desired
        self.exit_now = False
