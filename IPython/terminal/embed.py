# encoding: utf-8
"""
An embedded IPython shell.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import with_statement
from __future__ import print_function

import sys
import warnings

from IPython.core import ultratb, compilerop
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.interactiveshell import DummyMod
from IPython.core.interactiveshell import InteractiveShell
from IPython.terminal.interactiveshell import TerminalInteractiveShell
from IPython.terminal.ipapp import load_default_config

from traitlets import Bool, CBool, Unicode
from IPython.utils.io import ask_yes_no

class KillEmbeded(Exception):pass

# This is an additional magic that is exposed in embedded shells.
@magics_class
class EmbeddedMagics(Magics):

    @line_magic
    def kill_embedded(self, parameter_s=''):
        """%kill_embedded : deactivate for good the current embedded IPython.

        This function (after asking for confirmation) sets an internal flag so
        that an embedded IPython will never activate again.  This is useful to
        permanently disable a shell that is being called inside a loop: once
        you've figured out what you needed from it, you may then kill it and
        the program will then continue to run without the interactive shell
        interfering again.
        """

        kill = ask_yes_no("Are you sure you want to kill this embedded instance "
                         "(y/n)? [y/N] ",'n')
        if kill:
            self.shell.embedded_active = False
            print ("This embedded IPython will not reactivate anymore "
                   "once you exit.")


    @line_magic
    def exit_raise(self, parameter_s=''):
        """%exit_raise Make the current embedded kernel exit and raise and exception.

        This function sets an internal flag so that an embedded IPython will
        raise a `IPython.terminal.embed.KillEmbeded` Exception on exit, and then exit the current I. This is
        useful to permanently exit a loop that create IPython embed instance.
        """

        self.shell.should_raise = True
        self.shell.ask_exit()



class InteractiveShellEmbed(TerminalInteractiveShell):

    dummy_mode = Bool(False)
    exit_msg = Unicode('')
    embedded = CBool(True)
    embedded_active = CBool(True)
    should_raise = CBool(False)
    # Like the base class display_banner is not configurable, but here it
    # is True by default.
    display_banner = CBool(True)
    exit_msg = Unicode()
    

    def __init__(self, **kw):
        
    
        if kw.get('user_global_ns', None) is not None:
            warnings.warn("user_global_ns has been replaced by user_module. The\
                           parameter will be ignored, and removed in IPython 5.0", DeprecationWarning)

        super(InteractiveShellEmbed,self).__init__(**kw)

        # don't use the ipython crash handler so that user exceptions aren't
        # trapped
        sys.excepthook = ultratb.FormattedTB(color_scheme=self.colors,
                                             mode=self.xmode,
                                             call_pdb=self.pdb)

    def init_sys_modules(self):
        pass

    def init_magics(self):
        super(InteractiveShellEmbed, self).init_magics()
        self.register_magics(EmbeddedMagics)

    def __call__(self, header='', local_ns=None, module=None, dummy=None,
                 stack_depth=1, global_ns=None, compile_flags=None):
        """Activate the interactive interpreter.

        __call__(self,header='',local_ns=None,module=None,dummy=None) -> Start
        the interpreter shell with the given local and global namespaces, and
        optionally print a header string at startup.

        The shell can be globally activated/deactivated using the
        dummy_mode attribute. This allows you to turn off a shell used
        for debugging globally.

        However, *each* time you call the shell you can override the current
        state of dummy_mode with the optional keyword parameter 'dummy'. For
        example, if you set dummy mode on with IPShell.dummy_mode = True, you
        can still have a specific call work by making it as IPShell(dummy=False).
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
            self.set_readline_completer()

        # self.banner is auto computed
        if header:
            self.old_banner2 = self.banner2
            self.banner2 = self.banner2 + '\n' + header + '\n'
        else:
            self.old_banner2 = ''

        # Call the embedding code with a stack depth of 1 so it can skip over
        # our call and get the original caller's namespaces.
        self.mainloop(local_ns, module, stack_depth=stack_depth,
                      global_ns=global_ns, compile_flags=compile_flags)

        self.banner2 = self.old_banner2

        if self.exit_msg is not None:
            print(self.exit_msg)

        if self.should_raise:
            raise KillEmbeded('Embedded IPython raising error, as user requested.')


    def mainloop(self, local_ns=None, module=None, stack_depth=0,
                 display_banner=None, global_ns=None, compile_flags=None):
        """Embeds IPython into a running python program.

        Parameters
        ----------

        local_ns, module
          Working local namespace (a dict) and module (a module or similar
          object). If given as None, they are automatically taken from the scope
          where the shell was called, so that program variables become visible.

        stack_depth : int
          How many levels in the stack to go to looking for namespaces (when
          local_ns or module is None). This allows an intermediate caller to
          make sure that this function gets the namespace from the intended
          level in the stack. By default (0) it will get its locals and globals
          from the immediate caller.

        compile_flags
          A bit field identifying the __future__ features
          that are enabled, as passed to the builtin :func:`compile` function.
          If given as None, they are automatically taken from the scope where
          the shell was called.

        """
        
        if (global_ns is not None) and (module is None):
            warnings.warn("global_ns is deprecated, and will be removed in IPython 5.0 use module instead.", DeprecationWarning)
            module = DummyMod()
            module.__dict__ = global_ns

        # Get locals and globals from caller
        if ((local_ns is None or module is None or compile_flags is None)
            and self.default_user_namespaces):
            call_frame = sys._getframe(stack_depth).f_back

            if local_ns is None:
                local_ns = call_frame.f_locals
            if module is None:
                global_ns = call_frame.f_globals
                module = sys.modules[global_ns['__name__']]
            if compile_flags is None:
                compile_flags = (call_frame.f_code.co_flags &
                                 compilerop.PyCF_MASK)
        
        # Save original namespace and module so we can restore them after 
        # embedding; otherwise the shell doesn't shut down correctly.
        orig_user_module = self.user_module
        orig_user_ns = self.user_ns
        orig_compile_flags = self.compile.flags
        
        # Update namespaces and fire up interpreter
        
        # The global one is easy, we can just throw it in
        if module is not None:
            self.user_module = module

        # But the user/local one is tricky: ipython needs it to store internal
        # data, but we also need the locals. We'll throw our hidden variables
        # like _ih and get_ipython() into the local namespace, but delete them
        # later.
        if local_ns is not None:
            reentrant_local_ns = {k: v for (k, v) in local_ns.items() if k not in self.user_ns_hidden.keys()}
            self.user_ns = reentrant_local_ns
            self.init_user_ns()

        # Compiler flags
        if compile_flags is not None:
            self.compile.flags = compile_flags

        # make sure the tab-completer has the correct frame information, so it
        # actually completes using the frame's locals/globals
        self.set_completer_frame()

        with self.builtin_trap, self.display_trap:
            self.interact(display_banner=display_banner)
        
        # now, purge out the local namespace of IPython's hidden variables.
        if local_ns is not None:
            local_ns.update({k: v for (k, v) in self.user_ns.items() if k not in self.user_ns_hidden.keys()})

        
        # Restore original namespace so shell can shut down when we exit.
        self.user_module = orig_user_module
        self.user_ns = orig_user_ns
        self.compile.flags = orig_compile_flags


def embed(**kwargs):
    """Call this to embed IPython at the current point in your program.

    The first invocation of this will create an :class:`InteractiveShellEmbed`
    instance and then call it.  Consecutive calls just call the already
    created instance.

    If you don't want the kernel to initialize the namespace
    from the scope of the surrounding function,
    and/or you want to load full IPython configuration,
    you probably want `IPython.start_ipython()` instead.

    Here is a simple example::

        from IPython import embed
        a = 10
        b = 20
        embed(header='First time')
        c = 30
        d = 40
        embed()

    Full customization can be done by passing a :class:`Config` in as the
    config argument.
    """
    config = kwargs.get('config')
    header = kwargs.pop('header', u'')
    compile_flags = kwargs.pop('compile_flags', None)
    if config is None:
        config = load_default_config()
        config.InteractiveShellEmbed = config.TerminalInteractiveShell
        config.InteractiveShellEmbed.colors='nocolor'
        kwargs['config'] = config
    #save ps1/ps2 if defined
    ps1 = None
    ps2 = None
    try:
        ps1 = sys.ps1
        ps2 = sys.ps2
    except AttributeError:
        pass
    #save previous instance
    saved_shell_instance = InteractiveShell._instance
    if saved_shell_instance is not None:
        cls = type(saved_shell_instance)
        cls.clear_instance()
    shell = InteractiveShellEmbed.instance(**kwargs)
    shell(header=header, stack_depth=2, compile_flags=compile_flags)
    InteractiveShellEmbed.clear_instance()
    #restore previous instance
    if saved_shell_instance is not None:
        cls = type(saved_shell_instance)
        cls.clear_instance()
        for subclass in cls._walk_mro():
            subclass._instance = saved_shell_instance
    if ps1 is not None:
        sys.ps1 = ps1
        sys.ps2 = ps2
