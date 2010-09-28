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

from __future__ import with_statement
import __main__

import sys
from contextlib import nested

from IPython.core import ultratb
from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell
from IPython.frontend.terminal.ipapp import load_default_config

from IPython.utils.traitlets import Bool, Str, CBool
from IPython.utils.io import ask_yes_no


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


class InteractiveShellEmbed(TerminalInteractiveShell):

    dummy_mode = Bool(False)
    exit_msg = Str('')
    embedded = CBool(True)
    embedded_active = CBool(True)
    # Like the base class display_banner is not configurable, but here it
    # is True by default.
    display_banner = CBool(True)

    def __init__(self, config=None, ipython_dir=None, user_ns=None,
                 user_global_ns=None, custom_exceptions=((),None),
                 usage=None, banner1=None, banner2=None,
                 display_banner=None, exit_msg=u''):

        super(InteractiveShellEmbed,self).__init__(
            config=config, ipython_dir=ipython_dir, user_ns=user_ns,
            user_global_ns=user_global_ns, custom_exceptions=custom_exceptions,
            usage=usage, banner1=banner1, banner2=banner2,
            display_banner=display_banner
        )

        self.exit_msg = exit_msg
        self.define_magic("kill_embedded", kill_embedded)

        # don't use the ipython crash handler so that user exceptions aren't
        # trapped
        sys.excepthook = ultratb.FormattedTB(color_scheme=self.colors,
                                             mode=self.xmode,
                                             call_pdb=self.pdb)

    def init_sys_modules(self):
        pass

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

        if self.has_readline:
            self.set_completer()

        # self.banner is auto computed
        if header:
            self.old_banner2 = self.banner2
            self.banner2 = self.banner2 + '\n' + header + '\n'
        else:
            self.old_banner2 = ''

        # Call the embedding code with a stack depth of 1 so it can skip over
        # our call and get the original caller's namespaces.
        self.mainloop(local_ns, global_ns, stack_depth=stack_depth)

        self.banner2 = self.old_banner2

        if self.exit_msg is not None:
            print self.exit_msg

    def mainloop(self, local_ns=None, global_ns=None, stack_depth=0,
                 display_banner=None):
        """Embeds IPython into a running python program.

        Input:

          - header: An optional header message can be specified.

          - local_ns, global_ns: working namespaces. If given as None, the
          IPython-initialized one is updated with __main__.__dict__, so that
          program variables become visible but user-specific configuration
          remains possible.

          - stack_depth: specifies how many levels in the stack to go to
          looking for namespaces (when local_ns and global_ns are None).  This
          allows an intermediate caller to make sure that this function gets
          the namespace from the intended level in the stack.  By default (0)
          it will get its locals and globals from the immediate caller.

        Warning: it's possible to use this in a program which is being run by
        IPython itself (via %run), but some funny things will happen (a few
        globals get overwritten). In the future this will be cleaned up, as
        there is no fundamental reason why it can't work perfectly."""

        # Get locals and globals from caller
        if local_ns is None or global_ns is None:
            call_frame = sys._getframe(stack_depth).f_back

            if local_ns is None:
                local_ns = call_frame.f_locals
            if global_ns is None:
                global_ns = call_frame.f_globals

        # Update namespaces and fire up interpreter

        # The global one is easy, we can just throw it in
        self.user_global_ns = global_ns

        # but the user/local one is tricky: ipython needs it to store internal
        # data, but we also need the locals.  We'll copy locals in the user
        # one, but will track what got copied so we can delete them at exit.
        # This is so that a later embedded call doesn't see locals from a
        # previous call (which most likely existed in a separate scope).
        local_varnames = local_ns.keys()
        self.user_ns.update(local_ns)
        #self.user_ns['local_ns'] = local_ns  # dbg

        # Patch for global embedding to make sure that things don't overwrite
        # user globals accidentally. Thanks to Richard <rxe@renre-europe.com>
        # FIXME. Test this a bit more carefully (the if.. is new)
        if local_ns is None and global_ns is None:
            self.user_global_ns.update(__main__.__dict__)

        # make sure the tab-completer has the correct frame information, so it
        # actually completes using the frame's locals/globals
        self.set_completer_frame()

        with nested(self.builtin_trap, self.display_trap):
            self.interact(display_banner=display_banner)
        
            # now, purge out the user namespace from anything we might have added
            # from the caller's local namespace
            delvar = self.user_ns.pop
            for var in local_varnames:
                delvar(var,None)


_embedded_shell = None


def embed(**kwargs):
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
    config = kwargs.get('config')
    header = kwargs.pop('header', u'')
    if config is None:
        config = load_default_config()
        config.InteractiveShellEmbed = config.TerminalInteractiveShell
    global _embedded_shell
    if _embedded_shell is None:
        _embedded_shell = InteractiveShellEmbed(**kwargs)
    _embedded_shell(header=header, stack_depth=2)
