"""A ZMQ-based subclass of InteractiveShell.

This code is meant to ease the refactoring of the base InteractiveShell into
something with a cleaner architecture for 2-process use, without actually
breaking InteractiveShell itself.  So we're doing something a bit ugly, where
we subclass and override what we want to fix.  Once this is working well, we
can go back to the base class and refactor the code for a cleaner inheritance
implementation that doesn't rely on so much monkeypatching.

But this lets us maintain a fully working IPython as we develop the new
machinery.  This should thus be thought of as scaffolding.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import os
import sys
import time

from zmq.eventloop import ioloop

from IPython.core.interactiveshell import (
    InteractiveShell, InteractiveShellABC
)
from IPython.core import page
from IPython.core.autocall import ZMQExitAutocall
from IPython.core.displaypub import DisplayPublisher
from IPython.core.error import UsageError
from IPython.core.magics import MacroToEdit, CodeMagics
from IPython.core.magic import magics_class, line_magic, Magics
from IPython.core import payloadpage
from IPython.core.usage import default_gui_banner
from IPython.display import display, Javascript
from IPython.kernel.inprocess.socket import SocketABC
from IPython.kernel import (
    get_connection_file, get_connection_info, connect_qtconsole
)
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils import openpy
from IPython.utils.jsonutil import json_clean, encode_images
from IPython.utils.process import arg_split
from IPython.utils import py3compat
from IPython.utils.py3compat import unicode_type
from IPython.utils.traitlets import Instance, Type, Dict, CBool, CBytes, Any
from IPython.utils.warn import error
from IPython.kernel.zmq.displayhook import ZMQShellDisplayHook
from IPython.kernel.zmq.datapub import ZMQDataPublisher
from IPython.kernel.zmq.session import extract_header
from .session import Session

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

class ZMQDisplayPublisher(DisplayPublisher):
    """A display publisher that publishes data using a ZeroMQ PUB socket."""

    session = Instance(Session)
    pub_socket = Instance(SocketABC)
    parent_header = Dict({})
    topic = CBytes(b'display_data')

    def set_parent(self, parent):
        """Set the parent for outbound messages."""
        self.parent_header = extract_header(parent)
    
    def _flush_streams(self):
        """flush IO Streams prior to display"""
        sys.stdout.flush()
        sys.stderr.flush()

    def publish(self, data, metadata=None, source=None):
        self._flush_streams()
        if metadata is None:
            metadata = {}
        self._validate_data(data, metadata)
        content = {}
        content['data'] = encode_images(data)
        content['metadata'] = metadata
        self.session.send(
            self.pub_socket, u'display_data', json_clean(content),
            parent=self.parent_header, ident=self.topic,
        )

    def clear_output(self, wait=False):
        content = dict(wait=wait)
        self._flush_streams()
        self.session.send(
            self.pub_socket, u'clear_output', content,
            parent=self.parent_header, ident=self.topic,
        )

@magics_class
class KernelMagics(Magics):
    #------------------------------------------------------------------------
    # Magic overrides
    #------------------------------------------------------------------------
    # Once the base class stops inheriting from magic, this code needs to be
    # moved into a separate machinery as well.  For now, at least isolate here
    # the magics which this class needs to implement differently from the base
    # class, or that are unique to it.
    
    _find_edit_target = CodeMagics._find_edit_target

    @skip_doctest
    @line_magic
    def edit(self, parameter_s='', last_call=['','']):
        """Bring up an editor and execute the resulting code.

        Usage:
          %edit [options] [args]

        %edit runs an external text editor. You will need to set the command for
        this editor via the ``TerminalInteractiveShell.editor`` option in your
        configuration file before it will work.

        This command allows you to conveniently edit multi-line code right in
        your IPython session.

        If called without arguments, %edit opens up an empty editor with a
        temporary file and will execute the contents of this file when you
        close it (don't forget to save it!).

        Options:

        -n <number>
          Open the editor at a specified line number. By default, the IPython
          editor hook uses the unix syntax 'editor +N filename', but you can
          configure this by providing your own modified hook if your favorite
          editor supports line-number specifications with a different syntax.

        -p
          Call the editor with the same data as the previous time it was used,
          regardless of how long ago (in your current session) it was.

        -r
          Use 'raw' input. This option only applies to input taken from the
          user's history.  By default, the 'processed' history is used, so that
          magics are loaded in their transformed version to valid Python.  If
          this option is given, the raw input as typed as the command line is
          used instead.  When you exit the editor, it will be executed by
          IPython's own processor.

        Arguments:

        If arguments are given, the following possibilites exist:

        - The arguments are numbers or pairs of colon-separated numbers (like
          1 4:8 9). These are interpreted as lines of previous input to be
          loaded into the editor. The syntax is the same of the %macro command.

        - If the argument doesn't start with a number, it is evaluated as a
          variable and its contents loaded into the editor. You can thus edit
          any string which contains python code (including the result of
          previous edits).

        - If the argument is the name of an object (other than a string),
          IPython will try to locate the file where it was defined and open the
          editor at the point where it is defined. You can use ``%edit function``
          to load an editor exactly at the point where 'function' is defined,
          edit it and have the file be executed automatically.

          If the object is a macro (see %macro for details), this opens up your
          specified editor with a temporary file containing the macro's data.
          Upon exit, the macro is reloaded with the contents of the file.

          Note: opening at an exact line is only supported under Unix, and some
          editors (like kedit and gedit up to Gnome 2.8) do not understand the
          '+NUMBER' parameter necessary for this feature. Good editors like
          (X)Emacs, vi, jed, pico and joe all do.

        - If the argument is not found as a variable, IPython will look for a
          file with that name (adding .py if necessary) and load it into the
          editor. It will execute its contents with execfile() when you exit,
          loading any code in the file into your interactive namespace.

        Unlike in the terminal, this is designed to use a GUI editor, and we do
        not know when it has closed. So the file you edit will not be
        automatically executed or printed.

        Note that %edit is also available through the alias %ed.
        """

        opts,args = self.parse_options(parameter_s,'prn:')

        try:
            filename, lineno, _ = CodeMagics._find_edit_target(self.shell, args, opts, last_call)
        except MacroToEdit as e:
            # TODO: Implement macro editing over 2 processes.
            print("Macro editing not yet implemented in 2-process model.")
            return

        # Make sure we send to the client an absolute path, in case the working
        # directory of client and kernel don't match
        filename = os.path.abspath(filename)

        payload = {
            'source' : 'edit_magic',
            'filename' : filename,
            'line_number' : lineno
        }
        self.shell.payload_manager.write_payload(payload)

    # A few magics that are adapted to the specifics of using pexpect and a
    # remote terminal

    @line_magic
    def clear(self, arg_s):
        """Clear the terminal."""
        if os.name == 'posix':
            self.shell.system("clear")
        else:
            self.shell.system("cls")

    if os.name == 'nt':
        # This is the usual name in windows
        cls = line_magic('cls')(clear)

    # Terminal pagers won't work over pexpect, but we do have our own pager

    @line_magic
    def less(self, arg_s):
        """Show a file through the pager.

        Files ending in .py are syntax-highlighted."""
        if not arg_s:
            raise UsageError('Missing filename.')

        if arg_s.endswith('.py'):
            cont = self.shell.pycolorize(openpy.read_py_file(arg_s, skip_encoding_cookie=False))
        else:
            cont = open(arg_s).read()
        page.page(cont)

    more = line_magic('more')(less)

    # Man calls a pager, so we also need to redefine it
    if os.name == 'posix':
        @line_magic
        def man(self, arg_s):
            """Find the man page for the given command and display in pager."""
            page.page(self.shell.getoutput('man %s | col -b' % arg_s,
                                           split=False))

    @line_magic
    def connect_info(self, arg_s):
        """Print information for connecting other clients to this kernel
        
        It will print the contents of this session's connection file, as well as
        shortcuts for local clients.
        
        In the simplest case, when called from the most recently launched kernel,
        secondary clients can be connected, simply with:
        
        $> ipython <app> --existing
        
        """
        
        from IPython.core.application import BaseIPythonApplication as BaseIPApp
        
        if BaseIPApp.initialized():
            app = BaseIPApp.instance()
            security_dir = app.profile_dir.security_dir
            profile = app.profile
        else:
            profile = 'default'
            security_dir = ''
        
        try:
            connection_file = get_connection_file()
            info = get_connection_info(unpack=False)
        except Exception as e:
            error("Could not get connection info: %r" % e)
            return
        
        # add profile flag for non-default profile
        profile_flag = "--profile %s" % profile if profile != 'default' else ""
        
        # if it's in the security dir, truncate to basename
        if security_dir == os.path.dirname(connection_file):
            connection_file = os.path.basename(connection_file)
        
        
        print (info + '\n')
        print ("Paste the above JSON into a file, and connect with:\n"
            "    $> ipython <app> --existing <file>\n"
            "or, if you are local, you can connect with just:\n"
            "    $> ipython <app> --existing {0} {1}\n"
            "or even just:\n"
            "    $> ipython <app> --existing {1}\n"
            "if this is the most recent IPython session you have started.".format(
            connection_file, profile_flag
            )
        )

    @line_magic
    def qtconsole(self, arg_s):
        """Open a qtconsole connected to this kernel.
        
        Useful for connecting a qtconsole to running notebooks, for better
        debugging.
        """
        
        # %qtconsole should imply bind_kernel for engines:
        try:
            from IPython.parallel import bind_kernel
        except ImportError:
            # technically possible, because parallel has higher pyzmq min-version
            pass
        else:
            bind_kernel()
        
        try:
            p = connect_qtconsole(argv=arg_split(arg_s, os.name=='posix'))
        except Exception as e:
            error("Could not start qtconsole: %r" % e)
            return
    
    @line_magic
    def autosave(self, arg_s):
        """Set the autosave interval in the notebook (in seconds).
        
        The default value is 120, or two minutes.
        ``%autosave 0`` will disable autosave.
        
        This magic only has an effect when called from the notebook interface.
        It has no effect when called in a startup file.
        """
        
        try:
            interval = int(arg_s)
        except ValueError:
            raise UsageError("%%autosave requires an integer, got %r" % arg_s)
        
        # javascript wants milliseconds
        milliseconds = 1000 * interval
        display(Javascript("IPython.notebook.set_autosave_interval(%i)" % milliseconds),
            include=['application/javascript']
        )
        if interval:
            print("Autosaving every %i seconds" % interval)
        else:
            print("Autosave disabled")


class ZMQInteractiveShell(InteractiveShell):
    """A subclass of InteractiveShell for ZMQ."""

    displayhook_class = Type(ZMQShellDisplayHook)
    display_pub_class = Type(ZMQDisplayPublisher)
    data_pub_class = Type(ZMQDataPublisher)
    kernel = Any()
    parent_header = Any()
    
    def _banner1_default(self):
        return default_gui_banner

    # Override the traitlet in the parent class, because there's no point using
    # readline for the kernel. Can be removed when the readline code is moved
    # to the terminal frontend.
    colors_force = CBool(True)
    readline_use = CBool(False)
    # autoindent has no meaning in a zmqshell, and attempting to enable it
    # will print a warning in the absence of readline.
    autoindent = CBool(False)

    exiter = Instance(ZMQExitAutocall)
    def _exiter_default(self):
        return ZMQExitAutocall(self)
    
    def _exit_now_changed(self, name, old, new):
        """stop eventloop when exit_now fires"""
        if new:
            loop = ioloop.IOLoop.instance()
            loop.add_timeout(time.time()+0.1, loop.stop)

    keepkernel_on_exit = None

    # Over ZeroMQ, GUI control isn't done with PyOS_InputHook as there is no
    # interactive input being read; we provide event loop support in ipkernel
    @staticmethod
    def enable_gui(gui):
        from .eventloops import enable_gui as real_enable_gui
        try:
            real_enable_gui(gui)
        except ValueError as e:
            raise UsageError("%s" % e)

    def init_environment(self):
        """Configure the user's environment."""
        env = os.environ
        # These two ensure 'ls' produces nice coloring on BSD-derived systems
        env['TERM'] = 'xterm-color'
        env['CLICOLOR'] = '1'
        # Since normal pagers don't work at all (over pexpect we don't have
        # single-key control of the subprocess), try to disable paging in
        # subprocesses as much as possible.
        env['PAGER'] = 'cat'
        env['GIT_PAGER'] = 'cat'
    
    def init_hooks(self):
        super(ZMQInteractiveShell, self).init_hooks()
        self.set_hook('show_in_pager', page.as_hook(payloadpage.page), 99)
    
    def ask_exit(self):
        """Engage the exit actions."""
        self.exit_now = (not self.keepkernel_on_exit)
        payload = dict(
            source='ask_exit',
            keepkernel=self.keepkernel_on_exit,
            )
        self.payload_manager.write_payload(payload)

    def _showtraceback(self, etype, evalue, stb):
        # try to preserve ordering of tracebacks and print statements
        sys.stdout.flush()
        sys.stderr.flush()

        exc_content = {
            u'traceback' : stb,
            u'ename' : unicode_type(etype.__name__),
            u'evalue' : py3compat.safe_unicode(evalue),
        }

        dh = self.displayhook
        # Send exception info over pub socket for other clients than the caller
        # to pick up
        topic = None
        if dh.topic:
            topic = dh.topic.replace(b'execute_result', b'error')
        
        exc_msg = dh.session.send(dh.pub_socket, u'error', json_clean(exc_content), dh.parent_header, ident=topic)

        # FIXME - Hack: store exception info in shell object.  Right now, the
        # caller is reading this info after the fact, we need to fix this logic
        # to remove this hack.  Even uglier, we need to store the error status
        # here, because in the main loop, the logic that sets it is being
        # skipped because runlines swallows the exceptions.
        exc_content[u'status'] = u'error'
        self._reply_content = exc_content
        # /FIXME

        return exc_content

    def set_next_input(self, text, replace=False):
        """Send the specified text to the frontend to be presented at the next
        input cell."""
        payload = dict(
            source='set_next_input',
            text=text,
            replace=replace,
        )
        self.payload_manager.write_payload(payload)
    
    def set_parent(self, parent):
        """Set the parent header for associating output with its triggering input"""
        self.parent_header = parent
        self.displayhook.set_parent(parent)
        self.display_pub.set_parent(parent)
        self.data_pub.set_parent(parent)
        try:
            sys.stdout.set_parent(parent)
        except AttributeError:
            pass
        try:
            sys.stderr.set_parent(parent)
        except AttributeError:
            pass
    
    def get_parent(self):
        return self.parent_header
    
    #-------------------------------------------------------------------------
    # Things related to magics
    #-------------------------------------------------------------------------

    def init_magics(self):
        super(ZMQInteractiveShell, self).init_magics()
        self.register_magics(KernelMagics)
        self.magics_manager.register_alias('ed', 'edit')


InteractiveShellABC.register(ZMQInteractiveShell)
