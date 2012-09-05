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
import logging
import sys

# Local imports
from IPython.config.configurable import Configurable
from IPython.core.application import ProfileDir
from IPython.core.error import StdinNotImplementedError
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.utils.jsonutil import json_clean
from IPython.utils import py3compat
from IPython.utils.text import safe_unicode
from IPython.utils.traitlets import Any, Dict, Instance, List, Unicode
from kernelmagics import KernelMagics
from session import BaseSession

#-----------------------------------------------------------------------------
# Embedded kernel class
#-----------------------------------------------------------------------------

class EmbeddedKernel(Configurable):
    """ An embedded (in-process) IPython kernel.

    Rather than communicating with frontends via ZMQ, the embedded kernel talks
    directly to in-process frontends (represented as abstractly as
    EmbeddedKernelManagers).
    """

    #---------------------------------------------------------------------------
    # EmbeddedKernel interface
    #---------------------------------------------------------------------------

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    profile_dir = Instance('IPython.core.profiledir.ProfileDir')
    log = Instance(logging.Logger)

    session = Instance(BaseSession)
    def _session_default(self):
        return BaseSession(config=self.config)

    # The list of frontends "connected" to this kernel. These frontends receive
    # all messages on the pub/sub channel.
    frontends = List(
        Instance('IPython.embedded.kernel_manager.EmbeddedKernelManager'))
    
    user_module = Any()
    def _user_module_changed(self, name, old, new):
        if self.shell is not None:
            self.shell.user_module = new
    
    user_ns = Dict(default_value=None)
    def _user_ns_changed(self, name, old, new):
        if self.shell is not None:
            self.shell.user_ns = new
            self.shell.init_user_ns()

    def __init__(self, **kwargs):
        super(EmbeddedKernel, self).__init__(**kwargs)

        # Initialize the InteractiveShell subclass
        self.shell = EmbeddedInteractiveShell.instance(
            config      = self.config,
            profile_dir = self.profile_dir,
            user_module = self.user_module,
            user_ns     = self.user_ns)

    #---------------------------------------------------------------------------
    # EmbeddedKernel request methods
    #---------------------------------------------------------------------------

    # Each method has the same signature as the corresponding KernelManager
    # method, with two exceptions: 1) the first argument ('sender') is the
    # frontend making the request, and 2) the return value is a reply message.
    # The message conforms to the IPython messaging spec, but no parent header
    # is included.

    # FIXME: The execute() method duplicates a considerable amount of code from
    # IPython.zmq.ipkernel.Kernel. Is a refactor worthwhile?

    def execute_request(self, sender, code, silent=False, store_history=True,
                        user_variables=[], user_expressions={},
                        allow_stdin=True):
        """ Execute code in the kernel. """
        shell = self.shell

        # Replace raw_input. Note that is not sufficient to replace
        # raw_input in the user namespace.
        if allow_stdin:
            raw_input = lambda prompt='': self._raw_input(prompt, sender)
        else:
            raw_input = lambda prompt='' : self._no_raw_input()

        if py3compat.PY3:
            __builtin__.input = raw_input
        else:
            __builtin__.raw_input = raw_input

        # Execute the code.
        reply_content = {}
        try:
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

        return self.session.msg('execute_reply', json_clean(reply_content))

    def complete_request(self, sender, text, line, cursor_pos, block=None):
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

        return self.session.msg('complete_reply', json_clean(content))

    def object_info_request(self, sender, oname, detail_level=0):
        """ Get metadata information about an object. """
        content = self.shell.object_inspect(oname, detail_level)
        return self.session.msg('object_info_reply', json_clean(content))

    def history_request(self, sender, raw=True, output=False, 
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
        return self.session.msg('history_reply', json_clean(content))

    #---------------------------------------------------------------------------
    # EmbeddedKernel reply methods
    #---------------------------------------------------------------------------

    def input_reply(self, string):
        """ Submit raw input to the kernel. """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _no_raw_input(self):
        """ Raise StdinNotImplentedError if active frontend doesn't support
        stdin.
        """
        raise StdinNotImplementedError("raw_input was called, but this "
                                       "frontend does not support stdin.") 
        
    def _raw_input(self, prompt, sender):
        # Flush output before making the request.
        sys.stderr.flush()
        sys.stdout.flush()

        # Send the input request.
        content = json_clean(dict(prompt=prompt))
        raise NotImplementedError

#-----------------------------------------------------------------------------
# Embedded interactive shell class
#-----------------------------------------------------------------------------

class EmbeddedInteractiveShell(InteractiveShell):
    
    #---------------------------------------------------------------------------
    # InteractiveShell interface
    #---------------------------------------------------------------------------

    def init_magics(self):
        super(EmbeddedInteractiveShell, self).init_magics()
        self.register_magics(KernelMagics)
        self.magics_manager.register_alias('ed', 'edit')
    
    def _showtraceback(self, etype, evalue, stb):
        """ Actually show a traceback.
        """
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

InteractiveShellABC.register(EmbeddedInteractiveShell)
