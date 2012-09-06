""" An embedded (in-process) IPython kernel. """

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Standard library imports
import __builtin__
from contextlib import contextmanager
from io import IOBase
import logging
import sys
import traceback

# Local imports
from IPython.config.configurable import Configurable
from IPython.core.application import ProfileDir
from IPython.core.displayhook import DisplayHook
from IPython.core.error import StdinNotImplementedError
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.utils.jsonutil import encode_images, json_clean
from IPython.utils import py3compat
from IPython.utils.text import safe_unicode
from IPython.utils.traitlets import Any, Dict, Instance, List, Unicode
from kernelmagics import KernelMagics
from session import BaseSession

#-----------------------------------------------------------------------------
# Constants and trait definitions
#-----------------------------------------------------------------------------

FrontendTrait = Instance(
    'IPython.embedded.kernelmanager.EmbeddedKernelManager')

#-----------------------------------------------------------------------------
# Embedded kernel class
#-----------------------------------------------------------------------------

class EmbeddedKernel(Configurable):
    """ An embedded (in-process) IPython kernel.

    Rather than communicating with frontends via ZMQ, the embedded kernel talks
    directly to in-process frontends (represented as abstractly as
    EmbeddedKernelManagers).
    """

    # The list of frontends "connected" to this kernel. These frontends receive
    # all messages on the pub/sub channel.
    frontends = List(FrontendTrait)

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    session = Instance(BaseSession)
    profile_dir = Instance('IPython.core.profiledir.ProfileDir')
    log = Instance(logging.Logger)

    user_module = Any()
    user_ns = Dict(default_value=None)

    stdout = Any()
    stderr = Any()

    # Protected traits.
    _parent_frontend = FrontendTrait
    _parent_header = Dict()
    _raw_input_string = Any()

    #---------------------------------------------------------------------------
    # EmbeddedKernel public interface
    #---------------------------------------------------------------------------

    def __init__(self, **traits):
        # When an InteractiveShell is instantiated, it binds the current values
        # of sys.stdout and sys.stderr. Create the shell early and with the
        # redirected stdout/stderr.
        super(EmbeddedKernel, self).__init__(**traits)
        with self._redirected_io():
            self.shell

    def request(self, frontend, request_type, *args, **kwds):
        """ Make a request from a frontend.
        """
        assert frontend in self.frontends
        request_method = getattr(self, request_type)

        self._parent_frontend = frontend
        self._parent_header = frontend.session.msg_header(request_type)
        try:
            return request_method(*args, **kwds)
        finally:
            self._parent_frontend = self._parent_header = None

    #---------------------------------------------------------------------------
    # EmbeddedKernel request methods
    #---------------------------------------------------------------------------

    # Each method has the same signature as the corresponding KernelManager
    # method, except that the return value is a reply message. The message
    # conforms to the IPython messaging spec.

    # These methods should *not* be called directly, but rather accessed through
    # the generic ``request()`` method.

    # FIXME: The execute() method duplicates a considerable amount of code from
    # IPython.zmq.ipkernel.Kernel. Is a refactor worthwhile?

    def execute_request(self, code, silent=False, store_history=True,
                        user_variables=[], user_expressions={},
                        allow_stdin=True):
        """ Execute code in the kernel. """
        shell = self.shell

        # Execute the code.
        reply_content = {}
        try:
            with self._redirected_io(allow_stdin=allow_stdin):
                # FIXME: the shell calls the exception handler itself.
                shell.run_cell(code, store_history=store_history, silent=silent)
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

        # Return the execution counter so clients can display prompts.
        reply_content['execution_count'] = shell.execution_count - 1

        # FIXME - fish exception info out of shell, possibly left there by
        # runlines.  We'll need to clean up this logic later.
        if shell._reply_content is not None:
            reply_content.update(shell._reply_content)
            shell._reply_content = None

        # At this point, we can tell whether the main code execution succeeded
        # or not.  If it did, we proceed to evaluate user_variables/expressions
        if reply_content['status'] == 'ok':
            reply_content[u'user_variables'] = \
                shell.user_variables(user_variables)
            reply_content[u'user_expressions'] = \
                shell.user_expressions(user_expressions)
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

        return self.session.msg('execute_reply', json_clean(reply_content),
                                parent=self._parent_header)

    def complete_request(self, text, line, cursor_pos, block=None):
        """ Tab complete text in the kernel's namespace. """
        try:
            cursor_pos = int(cursor_pos)
        except:
            # If we don't get something that we can convert to an integer, at
            # least attempt the completion guessing the cursor is at the end of
            # the text, if there's any, and otherwise of the line
            cursor_pos = len(text)
            if cursor_pos == 0:
                cursor_pos = len(line)

        matched_text, matches = self.shell.complete(text, line, cursor_pos)
        content = dict(matches = matches,
                       matched_text = matched_text,
                       status = 'ok')

        return self.session.msg('complete_reply', json_clean(content),
                                parent=self._parent_header)

    def object_info_request(self, oname, detail_level=0):
        """ Get metadata information about an object. """
        content = self.shell.object_inspect(oname, detail_level)
        return self.session.msg('object_info_reply', json_clean(content),
                                parent=self._parent_header)

    def history_request(self, raw=True, output=False, 
                        hist_access_type='range', **kw):
        """ Get entries from the history list. """
        if hist_access_type == 'tail':
            n = kw['n']
            history = self.shell.history_manager.get_tail(
                n, raw=raw, output=output, include_latest=True)

        elif hist_access_type == 'range':
            session, start, stop = kw['session'], kw['start'], kw['stop']
            history = self.shell.history_manager.get_range(
                session, start, stop, raw=raw, output=output)

        elif hist_access_type == 'search':
            pattern = kw['pattern']
            history = self.shell.history_manager.search(
                pattern, raw=raw, output=output) 

        else:
            history = []

        content = dict(history=history)
        return self.session.msg('history_reply', json_clean(content),
                                parent=self._parent_header)

    #---------------------------------------------------------------------------
    # EmbeddedKernel reply methods
    #---------------------------------------------------------------------------

    def input_reply(self, string):
        """ Submit raw input to the kernel. """
        self._raw_input_string = string

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------
        
    def _raw_input(self, prompt):
        # Flush output before making the request.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the input request.
        content = json_clean(dict(prompt=prompt))
        msg = self.session.msg('input_request', content, self._parent_header)
        self._raw_input_string = None
        self._parent_frontend.stdin_channel.call_handlers(msg)

        # Receive input reply.
        while self._raw_input_string is None:
            self._parent_frontend.stdin_channel.process_events()
        return self._raw_input_string

    def _no_raw_input(self):
        """ Raise StdinNotImplentedError if active frontend doesn't support
        stdin.
        """
        raise StdinNotImplementedError("raw_input was called, but this "
                                       "frontend does not support stdin.")

    @contextmanager
    def _redirected_io(self, allow_stdin=True):
        # Replace raw_input. Note that is not sufficient to replace
        # raw_input in the user namespace.
        if allow_stdin:
            raw_input = lambda prompt='': self._raw_input(prompt)
        else:
            raw_input = lambda prompt='' : self._no_raw_input()
        if py3compat.PY3:
            sys_raw_input = __builtin__.input
            __builtin__.input = raw_input
        else:
            sys_raw_input = __builtin__.raw_input
            __builtin__.raw_input = raw_input

        # Replace stdout/stderr.
        sys_stdout, sys_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.stdout, self.stderr

        yield

        # Restore stdout/stderr.
        sys.stdout, sys.stderr = sys_stdout, sys_stderr
        
        # Restore raw_input.
        if py3compat.PY3:
            __builtin__.input = sys_raw_input
        else:
            __builtin__.raw_input = sys_raw_input

    #------ Trait initializers -----------------------------------------------

    def _session_default(self):
        return BaseSession(config=self.config)

    def _shell_default(self):
        return EmbeddedInteractiveShell.instance(
            kernel      = self,
            config      = self.config,
            profile_dir = self.profile_dir,
            user_module = self.user_module,
            user_ns     = self.user_ns)

    def _stdout_default(self):
        return EmbeddedOutStream(self, 'stdout')

    def _stderr_default(self):
        return EmbeddedOutStream(self, 'stderr')

    #------ Trait change handlers --------------------------------------------

    def _user_module_changed(self, name, old, new):
        if self.shell is not None:
            self.shell.user_module = new

    def _user_ns_changed(self, name, old, new):
        if self.shell is not None:
            self.shell.user_ns = new
            self.shell.init_user_ns()

#-----------------------------------------------------------------------------
# Embedded interactive shell class
#-----------------------------------------------------------------------------

class EmbeddedInteractiveShell(InteractiveShell):

    def __init__(self, kernel, *args, **kwds):
        super(EmbeddedInteractiveShell, self).__init__(*args, **kwds)
        self.kernel = kernel
        self._reply_content = None
    
    #---------------------------------------------------------------------------
    # InteractiveShell interface
    #---------------------------------------------------------------------------

    def init_magics(self):
        super(EmbeddedInteractiveShell, self).init_magics()
        self.register_magics(KernelMagics)
        self.magics_manager.register_alias('ed', 'edit')

    def init_sys_modules(self):
        # Don't take over the runtime environment.
        pass

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------
        
    def _showtraceback(self, etype, evalue, stb):
        """ Actually show a traceback.
        """
        exc_content = {
            u'traceback' : stb,
            u'ename' : unicode(etype.__name__),
            u'evalue' : safe_unicode(evalue)
        }

        kernel = self.kernel
        exc_msg = kernel.session.msg('pyerr', json_clean(exc_content),
                                     parent=kernel._parent_header)
        for frontend in kernel.frontends:
            frontend.sub_channel.call_handlers(exc_msg)

        # FIXME - Hack: store exception info in shell object.  Right now, the
        # caller is reading this info after the fact, we need to fix this logic
        # to remove this hack.  Even uglier, we need to store the error status
        # here, because in the main loop, the logic that sets it is being
        # skipped because runlines swallows the exceptions.
        exc_content[u'status'] = u'error'
        self._reply_content = exc_content
        # /FIXME

        return exc_content

    #------ Trait initializers -----------------------------------------------

    def _displayhook_class_default(self):
        return EmbeddedDisplayHook

InteractiveShellABC.register(EmbeddedInteractiveShell)

#-----------------------------------------------------------------------------
# IO streams and display hook
#-----------------------------------------------------------------------------

class EmbeddedOutStream(IOBase):

    def __init__(self, kernel, name):
        super(EmbeddedOutStream, self).__init__()
        self.kernel = kernel
        self.name = name

    def writable(self):
        return True

    def write(self, string):
        content = dict(name=self.name, data=string)
        parent = self.kernel._parent_header
        msg = self.kernel.session.msg('stream', content, parent=parent)
        for frontend in self.kernel.frontends:
            frontend.sub_channel.call_handlers(msg)

class EmbeddedDisplayHook(DisplayHook):

    def start_displayhook(self):
        kernel = self.shell.kernel
        self.msg = kernel.session.msg(u'pyout', {}, kernel._parent_header)

    def write_output_prompt(self):
        self.msg['content']['execution_count'] = self.prompt_count

    def write_format_data(self, format_dict):
        self.msg['content']['data'] = encode_images(format_dict)

    def finish_displayhook(self):
        kernel = self.shell.kernel
        kernel.stdout.flush()
        kernel.stderr.flush()
        for frontend in kernel.frontends:
            frontend.sub_channel.call_handlers(self.msg)
        self.msg = None
