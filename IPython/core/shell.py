#!/usr/bin/env python
# encoding: utf-8
"""IPython Shell classes.

Originally, this module was horribly complicated because of the need to
use threads to integrate with GUI toolkit event loops.  Now, we are using
the :mod:`IPython.lib.inputhook`, which is based on PyOS_InputHook.  This
dramatically simplifies this logic and allow 3rd party packages (such as
matplotlib) to handle these things by themselves.

This new approach also allows projects like matplotlib to work interactively
in the standard python shell.
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
from IPython.core import ipapi
from IPython.utils.genutils import ask_yes_no
from IPython.core.iplib import InteractiveShell
from IPython.core.ipmaker import make_IPython

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class IPShell:
    """Create an IPython instance.

    This calls the factory :func:`make_IPython`, which creates a configured
    :class:`InteractiveShell` object, and presents the result as a simple 
    class with a :meth:`mainloop` method.
    """

    def __init__(self, argv=None, user_ns=None, user_global_ns=None,
                 debug=1, shell_class=InteractiveShell):
        self.IP = make_IPython(argv, user_ns=user_ns,
                               user_global_ns=user_global_ns,
                               debug=debug, shell_class=shell_class)

    def mainloop(self,sys_exit=0,banner=None):
        self.IP.mainloop(banner)
        if sys_exit:
            sys.exit()


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
        self.shell.embedded_active = False
        print "This embedded IPython will not reactivate anymore once you exit."


class IPShellEmbed:
    """Allow embedding an IPython shell into a running program.

    Instances of this class are callable, with the __call__ method being an
    alias to the embed() method of an InteractiveShell instance.

    Usage (see also the example-embed.py file for a running example)::

        ipshell = IPShellEmbed([argv,banner,exit_msg,rc_override])

    * argv: list containing valid command-line options for IPython, as they
    would appear in sys.argv[1:].

    For example, the following command-line options::

        $ ipython -prompt_in1 'Input <\\#>' -colors LightBG

    would be passed in the argv list as::

        ['-prompt_in1','Input <\\#>','-colors','LightBG']

    * banner: string which gets printed every time the interpreter starts.

    * exit_msg: string which gets printed every time the interpreter exits.

    * rc_override: a dict or Struct of configuration options such as those
    used by IPython. These options are read from your ~/.ipython/ipythonrc
    file when the Shell object is created. Passing an explicit rc_override
    dict with any options you want allows you to override those values at
    creation time without having to modify the file. This way you can create
    embeddable instances configured in any way you want without editing any
    global files (thus keeping your interactive IPython configuration
    unchanged).

    Then the ipshell instance can be called anywhere inside your code::
    
        ipshell(header='') -> Opens up an IPython shell.

    * header: string printed by the IPython shell upon startup. This can let
    you know where in your code you are when dropping into the shell. Note
    that 'banner' gets prepended to all calls, so header is used for
    location-specific information.

    For more details, see the __call__ method below.

    When the IPython shell is exited with Ctrl-D, normal program execution
    resumes.

    This functionality was inspired by a posting on comp.lang.python by cmkl
    <cmkleffner@gmx.de> on Dec. 06/01 concerning similar uses of pyrepl, and
    by the IDL stop/continue commands.
    """

    def __init__(self, argv=None, banner='', exit_msg=None, 
                 rc_override=None, user_ns=None):
        """Note that argv here is a string, NOT a list."""

        self.set_banner(banner)
        self.set_exit_msg(exit_msg)
        self.set_dummy_mode(0)

        # sys.displayhook is a global, we need to save the user's original
        # Don't rely on __displayhook__, as the user may have changed that.
        self.sys_displayhook_ori = sys.displayhook

        # save readline completer status
        try:
            #print 'Save completer',sys.ipcompleter  # dbg
            self.sys_ipcompleter_ori = sys.ipcompleter
        except:
            pass # not nested with IPython
        
        self.IP = make_IPython(argv,rc_override=rc_override,
                               embedded=True,
                               user_ns=user_ns)

        ip = ipapi.IPApi(self.IP)
        ip.expose_magic("kill_embedded",kill_embedded)

        # copy our own displayhook also
        self.sys_displayhook_embed = sys.displayhook
        # and leave the system's display hook clean
        sys.displayhook = self.sys_displayhook_ori
        # don't use the ipython crash handler so that user exceptions aren't
        # trapped
        sys.excepthook = ultratb.FormattedTB(color_scheme = self.IP.colors,
                                             mode = self.IP.xmode,
                                             call_pdb = self.IP.pdb)
        self.restore_system_completer()

    def restore_system_completer(self):
        """Restores the readline completer which was in place.

        This allows embedded IPython within IPython not to disrupt the
        parent's completion.
        """
        
        try:
            self.IP.readline.set_completer(self.sys_ipcompleter_ori)
            sys.ipcompleter = self.sys_ipcompleter_ori
        except:
            pass

    def __call__(self, header='', local_ns=None, global_ns=None, dummy=None):
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
        if not self.IP.embedded_active:
            return

        # Normal exits from interactive mode set this flag, so the shell can't
        # re-enter (it checks this variable at the start of interactive mode).
        self.IP.exit_now = False

        # Allow the dummy parameter to override the global __dummy_mode
        if dummy or (dummy != 0 and self.__dummy_mode):
            return

        # Set global subsystems (display,completions) to our values
        sys.displayhook = self.sys_displayhook_embed
        if self.IP.has_readline:
            self.IP.set_completer()

        if self.banner and header:
            format = '%s\n%s\n'
        else:
            format = '%s%s\n'
        banner =  format % (self.banner,header)

        # Call the embedding code with a stack depth of 1 so it can skip over
        # our call and get the original caller's namespaces.
        self.IP.embed_mainloop(banner,local_ns,global_ns,stack_depth=1)

        if self.exit_msg:
            print self.exit_msg
            
        # Restore global systems (display, completion)
        sys.displayhook = self.sys_displayhook_ori
        self.restore_system_completer()
    
    def set_dummy_mode(self, dummy):
        """Sets the embeddable shell's dummy mode parameter.

        set_dummy_mode(dummy): dummy = 0 or 1.

        This parameter is persistent and makes calls to the embeddable shell
        silently return without performing any action. This allows you to
        globally activate or deactivate a shell you're using with a single call.

        If you need to manually"""

        if dummy not in [0,1,False,True]:
            raise ValueError,'dummy parameter must be boolean'
        self.__dummy_mode = dummy

    def get_dummy_mode(self):
        """Return the current value of the dummy mode parameter.
        """
        return self.__dummy_mode
    
    def set_banner(self, banner):
        """Sets the global banner.

        This banner gets prepended to every header printed when the shell
        instance is called."""

        self.banner = banner

    def set_exit_msg(self, exit_msg):
        """Sets the global exit_msg.

        This exit message gets printed upon exiting every time the embedded
        shell is called. It is None by default. """

        self.exit_msg = exit_msg

# This is the one which should be called by external code.
def start(user_ns = None):
    """Return a running shell instance of :class:`IPShell`."""
    return IPShell(user_ns = user_ns)

