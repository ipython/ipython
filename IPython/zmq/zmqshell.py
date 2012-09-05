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
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib
import os
import sys
import time

# System library imports
from zmq.eventloop import ioloop

# Our own
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.core import page
from IPython.core.autocall import ZMQExitAutocall
from IPython.core.displaypub import DisplayPublisher
from IPython.core.error import UsageError
from IPython.core.magic import magics_class, line_magic
from IPython.core.payloadpage import install_payload_page
from IPython.embedded.kernelmagics import KernelMagics
from IPython.lib.kernel import (
    get_connection_file, get_connection_info, connect_qtconsole
)
from IPython.utils.jsonutil import json_clean, encode_images
from IPython.utils.process import arg_split
from IPython.utils import py3compat
from IPython.utils.text import safe_unicode
from IPython.utils.traitlets import Instance, Type, Dict, CBool, CBytes
from IPython.utils.warn import warn, error
from IPython.zmq.displayhook import ZMQShellDisplayHook
from IPython.zmq.datapub import ZMQDataPublisher
from IPython.zmq.session import extract_header
from session import Session

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

class ZMQDisplayPublisher(DisplayPublisher):
    """A display publisher that publishes data using a ZeroMQ PUB socket."""

    session = Instance(Session)
    pub_socket = Instance('zmq.Socket')
    parent_header = Dict({})
    topic = CBytes(b'displaypub')

    def set_parent(self, parent):
        """Set the parent for outbound messages."""
        self.parent_header = extract_header(parent)
    
    def _flush_streams(self):
        """flush IO Streams prior to display"""
        sys.stdout.flush()
        sys.stderr.flush()

    def publish(self, source, data, metadata=None):
        self._flush_streams()
        if metadata is None:
            metadata = {}
        self._validate_data(source, data, metadata)
        content = {}
        content['source'] = source
        content['data'] = encode_images(data)
        content['metadata'] = metadata
        self.session.send(
            self.pub_socket, u'display_data', json_clean(content),
            parent=self.parent_header, ident=self.topic,
        )

    def clear_output(self, stdout=True, stderr=True, other=True):
        content = dict(stdout=stdout, stderr=stderr, other=other)
        
        if stdout:
            print('\r', file=sys.stdout, end='')
        if stderr:
            print('\r', file=sys.stderr, end='')
        
        self._flush_streams()
        
        self.session.send(
            self.pub_socket, u'clear_output', content,
            parent=self.parent_header, ident=self.topic,
        )


@magics_class
class ZMQKernelMagics(KernelMagics):

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
            "if this is the most recent IPython session "
            "you have started.".format(connection_file, profile_flag))

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


class ZMQInteractiveShell(InteractiveShell):
    """A subclass of InteractiveShell for ZMQ."""

    displayhook_class = Type(ZMQShellDisplayHook)
    display_pub_class = Type(ZMQDisplayPublisher)
    data_pub_class = Type(ZMQDataPublisher)

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
    from .eventloops import enable_gui
    enable_gui = staticmethod(enable_gui)

    def init_environment(self):
        """Configure the user's environment.

        """
        env = os.environ
        # These two ensure 'ls' produces nice coloring on BSD-derived systems
        env['TERM'] = 'xterm-color'
        env['CLICOLOR'] = '1'
        # Since normal pagers don't work at all (over pexpect we don't have
        # single-key control of the subprocess), try to disable paging in
        # subprocesses as much as possible.
        env['PAGER'] = 'cat'
        env['GIT_PAGER'] = 'cat'
        
        # And install the payload version of page.
        install_payload_page()

    def auto_rewrite_input(self, cmd):
        """Called to show the auto-rewritten input for autocall and friends.

        FIXME: this payload is currently not correctly processed by the
        frontend.
        """
        new = self.prompt_manager.render('rewrite') + cmd
        payload = dict(
            source='IPython.zmq.zmqshell.ZMQInteractiveShell.auto_rewrite_input',
            transformed_input=new,
            )
        self.payload_manager.write_payload(payload)

    def ask_exit(self):
        """Engage the exit actions."""
        self.exit_now = True
        payload = dict(
            source='IPython.zmq.zmqshell.ZMQInteractiveShell.ask_exit',
            exit=True,
            keepkernel=self.keepkernel_on_exit,
            )
        self.payload_manager.write_payload(payload)

    def _showtraceback(self, etype, evalue, stb):

        exc_content = {
            u'traceback' : stb,
            u'ename' : unicode(etype.__name__),
            u'evalue' : safe_unicode(evalue)
        }

        dh = self.displayhook
        # Send exception info over pub socket for other clients than the caller
        # to pick up
        topic = None
        if dh.topic:
            topic = dh.topic.replace(b'pyout', b'pyerr')
        
        exc_msg = dh.session.send(dh.pub_socket, u'pyerr', json_clean(exc_content), dh.parent_header, ident=topic)

        # FIXME - Hack: store exception info in shell object.  Right now, the
        # caller is reading this info after the fact, we need to fix this logic
        # to remove this hack.  Even uglier, we need to store the error status
        # here, because in the main loop, the logic that sets it is being
        # skipped because runlines swallows the exceptions.
        exc_content[u'status'] = u'error'
        self._reply_content = exc_content
        # /FIXME

        return exc_content

    def set_next_input(self, text):
        """Send the specified text to the frontend to be presented at the next
        input cell."""
        payload = dict(
            source='IPython.zmq.zmqshell.ZMQInteractiveShell.set_next_input',
            text=text
        )
        self.payload_manager.write_payload(payload)
    
    #-------------------------------------------------------------------------
    # Things related to magics
    #-------------------------------------------------------------------------

    def init_magics(self):
        super(ZMQInteractiveShell, self).init_magics()
        self.register_magics(ZMQKernelMagics)
        self.magics_manager.register_alias('ed', 'edit')


InteractiveShellABC.register(ZMQInteractiveShell)
