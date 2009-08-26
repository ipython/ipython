#!/usr/bin/env python
# encoding: utf-8
"""
An embedded IPython shell.

Authors:

* Brian Granger
* Fernando Perez

Notes
-----
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys

from IPython.core import ultratb
from IPython.core.iplib import InteractiveShell

from IPython.utils.traitlets import Bool, Str, CBool
from IPython.utils.genutils import ask_yes_no

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

# This is an additional magic that is exposed in embedded shells.
def kill_embedded(self,parameter_s=''):
    """%kill_embedded : deactivate for good the current embedded IPython.

    This function (after asking for confirmation) sets an internal flag so that
    an embedded IPython will never activate again.  This is useful to
    permanently disable a shell that is being called inside a loop: once you've
    figured out what you needed from it, you may then kill it and the program
    will then continue to run without the interactive shell interfering again.
    """
    
    kill = ask_yes_no("Are you sure you want to kill this embedded instance "
                     "(y/n)? [y/N] ",'n')
    if kill:
        self.embedded_active = False
        print "This embedded IPython will not reactivate anymore once you exit."


class InteractiveShellEmbed(InteractiveShell):

    dummy_mode = Bool(False)
    exit_msg = Str('')
    embedded = CBool(True)
    embedded_active = CBool(True)

    def __init__(self, parent=None, config=None, ipythondir=None, usage=None,
                 user_ns=None, user_global_ns=None,
                 banner1=None, banner2=None,
                 custom_exceptions=((),None), exit_msg=None):

        # First we need to save the state of sys.displayhook and
        # sys.ipcompleter so we can restore it when we are done.
        self.save_sys_displayhook()
        self.save_sys_ipcompleter()

        super(InteractiveShellEmbed,self).__init__(
            parent=parent, config=config, ipythondir=ipythondir, usage=usage, 
            user_ns=user_ns, user_global_ns=user_global_ns,
            banner1=banner1, banner2=banner2, 
            custom_exceptions=custom_exceptions)

        self.save_sys_displayhook_embed()
        self.exit_msg = exit_msg
        self.define_magic("kill_embedded", kill_embedded)

        # don't use the ipython crash handler so that user exceptions aren't
        # trapped
        sys.excepthook = ultratb.FormattedTB(color_scheme=self.colors,
                                             mode=self.xmode,
                                             call_pdb=self.pdb)

        self.restore_sys_displayhook()
        self.restore_sys_ipcompleter()

    def init_sys_modules(self):
        pass

    def save_sys_displayhook(self):
        # sys.displayhook is a global, we need to save the user's original
        # Don't rely on __displayhook__, as the user may have changed that.
        self.sys_displayhook_orig = sys.displayhook

    def save_sys_ipcompleter(self):
        """Save readline completer status."""
        try:
            #print 'Save completer',sys.ipcompleter  # dbg
            self.sys_ipcompleter_orig = sys.ipcompleter
        except:
            pass # not nested with IPython        

    def restore_sys_displayhook(self):
        sys.displayhook = self.sys_displayhook_orig

    def restore_sys_ipcompleter(self):
        """Restores the readline completer which was in place.

        This allows embedded IPython within IPython not to disrupt the
        parent's completion.
        """
        try:
            self.readline.set_completer(self.sys_ipcompleter_orig)
            sys.ipcompleter = self.sys_ipcompleter_orig
        except:
            pass

    def save_sys_displayhook_embed(self):
        self.sys_displayhook_embed = sys.displayhook

    def restore_sys_displayhook_embed(self):
        sys.displayhook = self.sys_displayhook_embed

    def __call__(self, header='', local_ns=None, global_ns=None, dummy=None,
                 stack_depth=1):
        """Activate the interactive interpreter.

        __call__(self,header='',local_ns=None,global_ns,dummy=None) -> Start
        the interpreter shell with the given local and global namespaces, and
        optionally print a header string at startup.

        The shell can be globally activated/deactivated using the
        set/get_dummy_mode methods. This allows you to turn off a shell used
        for debugging globally.

        However, *each* time you call the shell you can override the current
        state of dummy_mode with the optional keyword parameter 'dummy'. For
        example, if you set dummy mode on with IPShell.set_dummy_mode(1), you
        can still have a specific call work by making it as IPShell(dummy=0).

        The optional keyword parameter dummy controls whether the call
        actually does anything.
        """

        # If the user has turned it off, go away
        if not self.embedded_active:
            return

        # Normal exits from interactive mode set this flag, so the shell can't
        # re-enter (it checks this variable at the start of interactive mode).
        self.exit_now = False

        # Allow the dummy parameter to override the global __dummy_mode
        if dummy or (dummy != 0 and self.dummy_mode):
            return

        self.restore_sys_displayhook_embed()

        if self.has_readline:
            self.set_completer()

        if self.banner and header:
            format = '%s\n%s\n'
        else:
            format = '%s%s\n'
        banner =  format % (self.banner,header)

        # Call the embedding code with a stack depth of 1 so it can skip over
        # our call and get the original caller's namespaces.
        self.embed_mainloop(banner, local_ns, global_ns, 
                            stack_depth=stack_depth)

        if self.exit_msg is not None:
            print self.exit_msg
            
        # Restore global systems (display, completion)
        self.restore_sys_displayhook()
        self.restore_sys_ipcompleter()


_embedded_shell = None


def embed(header='', config=None, usage=None, banner1=None, banner2=None,
          exit_msg=''):
    """Call this to embed IPython at the current point in your program.

    The first invocation of this will create an :class:`InteractiveShellEmbed`
    instance and then call it.  Consecutive calls just call the already
    created instance.

    Here is a simple example::

        from IPython import embed
        a = 10
        b = 20
        embed('First time')
        c = 30
        d = 40
        embed

    Full customization can be done by passing a :class:`Struct` in as the 
    config argument.
    """
    global _embedded_shell
    if _embedded_shell is None:
        _embedded_shell = InteractiveShellEmbed(config=config,
        usage=usage, banner1=banner1, banner2=banner2, exit_msg=exit_msg)
    _embedded_shell(header=header, stack_depth=2)

