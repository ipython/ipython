# -*- coding: utf-8 -*-
"""Subclass of InteractiveShell for terminal based frontends."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de>
#  Copyright (C) 2001-2007 Fernando Perez. <fperez@colorado.edu>
#  Copyright (C) 2008-2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__
import bdb
from contextlib import nested
import os
import re
import sys

from IPython.core.error import TryNext
from IPython.core.usage import interactive_usage, default_banner
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.lib.inputhook import enable_gui
from IPython.lib.pylabtools import pylab_activate
from IPython.testing import decorators as testdec
from IPython.utils.terminal import toggle_set_term_title, set_term_title
from IPython.utils.process import abbrev_cwd
from IPython.utils.warn import warn
from IPython.utils.text import num_ini_spaces
from IPython.utils.traitlets import Int, Str, CBool, Unicode

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

def get_default_editor():
    try:
        ed = os.environ['EDITOR']
    except KeyError:
        if os.name == 'posix':
            ed = 'vi'  # the only one guaranteed to be there!
        else:
            ed = 'notepad' # same in Windows!
    return ed


# store the builtin raw_input globally, and use this always, in case user code
# overwrites it (like wx.py.PyShell does)
raw_input_original = raw_input

#-----------------------------------------------------------------------------
# Main class
#-----------------------------------------------------------------------------

class TerminalInteractiveShell(InteractiveShell):

    autoedit_syntax = CBool(False, config=True,
        help="auto editing of files with syntax errors.")
    banner = Unicode('')
    banner1 = Unicode(default_banner, config=True,
        help="""The part of the banner to be printed before the profile"""
    )
    banner2 = Unicode('', config=True,
        help="""The part of the banner to be printed after the profile"""
    )
    confirm_exit = CBool(True, config=True,
        help="""
        Set to confirm when you try to exit IPython with an EOF (Control-D
        in Unix, Control-Z/Enter in Windows). By typing 'exit' or 'quit',
        you can force a direct exit without any confirmation.""",
    )
    # This display_banner only controls whether or not self.show_banner()
    # is called when mainloop/interact are called.  The default is False
    # because for the terminal based application, the banner behavior
    # is controlled by Global.display_banner, which IPythonApp looks at
    # to determine if *it* should call show_banner() by hand or not.
    display_banner = CBool(False) # This isn't configurable!
    embedded = CBool(False)
    embedded_active = CBool(False)
    editor = Unicode(get_default_editor(), config=True,
        help="Set the editor used by IPython (default to $EDITOR/vi/notepad)."
    )
    pager = Unicode('less', config=True,
        help="The shell program to be used for paging.")

    screen_length = Int(0, config=True,
        help=
        """Number of lines of your screen, used to control printing of very
        long strings.  Strings longer than this number of lines will be sent
        through a pager instead of directly printed.  The default value for
        this is 0, which means IPython will auto-detect your screen size every
        time it needs to print certain potentially long strings (this doesn't
        change the behavior of the 'print' keyword, it's only triggered
        internally). If for some reason this isn't working well (it needs
        curses support), specify it yourself. Otherwise don't change the
        default.""",
    )
    term_title = CBool(False, config=True,
        help="Enable auto setting the terminal title."
    )

    def __init__(self, config=None, ipython_dir=None, profile_dir=None, user_ns=None,
                 user_global_ns=None, custom_exceptions=((),None),
                 usage=None, banner1=None, banner2=None,
                 display_banner=None):

        super(TerminalInteractiveShell, self).__init__(
            config=config, profile_dir=profile_dir, user_ns=user_ns,
            user_global_ns=user_global_ns, custom_exceptions=custom_exceptions
        )
        self.init_term_title()
        self.init_usage(usage)
        self.init_banner(banner1, banner2, display_banner)

    #-------------------------------------------------------------------------
    # Things related to the terminal
    #-------------------------------------------------------------------------

    @property
    def usable_screen_length(self):
        if self.screen_length == 0:
            return 0
        else:
            num_lines_bot = self.separate_in.count('\n')+1
            return self.screen_length - num_lines_bot

    def init_term_title(self):
        # Enable or disable the terminal title.
        if self.term_title:
            toggle_set_term_title(True)
            set_term_title('IPython: ' + abbrev_cwd())
        else:
            toggle_set_term_title(False)

    #-------------------------------------------------------------------------
    # Things related to aliases
    #-------------------------------------------------------------------------

    def init_alias(self):
        # The parent class defines aliases that can be safely used with any
        # frontend.
        super(TerminalInteractiveShell, self).init_alias()

        # Now define aliases that only make sense on the terminal, because they
        # need direct access to the console in a way that we can't emulate in
        # GUI or web frontend
        if os.name == 'posix':
            aliases = [('clear', 'clear'), ('more', 'more'), ('less', 'less'),
                       ('man', 'man')]
        elif os.name == 'nt':
            aliases = [('cls', 'cls')]


        for name, cmd in aliases:
            self.alias_manager.define_alias(name, cmd)

    #-------------------------------------------------------------------------
    # Things related to the banner and usage
    #-------------------------------------------------------------------------

    def _banner1_changed(self):
        self.compute_banner()

    def _banner2_changed(self):
        self.compute_banner()

    def _term_title_changed(self, name, new_value):
        self.init_term_title()

    def init_banner(self, banner1, banner2, display_banner):
        if banner1 is not None:
            self.banner1 = banner1
        if banner2 is not None:
            self.banner2 = banner2
        if display_banner is not None:
            self.display_banner = display_banner
        self.compute_banner()

    def show_banner(self, banner=None):
        if banner is None:
            banner = self.banner
        self.write(banner)

    def compute_banner(self):
        self.banner = self.banner1
        if self.profile:
            self.banner += '\nIPython profile: %s\n' % self.profile
        if self.banner2:
            self.banner += '\n' + self.banner2

    def init_usage(self, usage=None):
        if usage is None:
            self.usage = interactive_usage
        else:
            self.usage = usage

    #-------------------------------------------------------------------------
    # Mainloop and code execution logic
    #-------------------------------------------------------------------------

    def mainloop(self, display_banner=None):
        """Start the mainloop.

        If an optional banner argument is given, it will override the
        internally created default banner.
        """
        
        with nested(self.builtin_trap, self.display_trap):

            while 1:
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
        if display_banner:
            self.show_banner()

        more = False
        
        # Mark activity in the builtins
        __builtin__.__dict__['__IPYTHON__active'] += 1
        
        if self.has_readline:
            self.readline_startup_hook(self.pre_readline)
        # exit_now is set by a call to %Exit or %Quit, through the
        # ask_exit callback.

        while not self.exit_now:
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
                    source_raw = self.input_splitter.source_raw_reset()[1]
                    self.run_cell(source_raw)
                
        # We are off again...
        __builtin__.__dict__['__IPYTHON__active'] -= 1

        # Turn off the exit flag, so the mainloop can be restarted if desired
        self.exit_now = False

    def raw_input(self, prompt=''):
        """Write a prompt and read a line.

        The returned line does not include the trailing newline.
        When the user enters the EOF key sequence, EOFError is raised.

        Optional inputs:

          - prompt(''): a string to be printed to prompt the user.

          - continue_prompt(False): whether this line is the first one or a
          continuation in a sequence of inputs.
        """
        # Code run by the user may have modified the readline completer state.
        # We must ensure that our completer is back in place.

        if self.has_readline:
            self.set_readline_completer()
        
        try:
            line = raw_input_original(prompt).decode(self.stdin_encoding)
        except ValueError:
            warn("\n********\nYou or a %run:ed script called sys.stdin.close()"
                 " or sys.stdout.close()!\nExiting IPython!")
            self.ask_exit()
            return ""

        # Try to be reasonably smart about not re-indenting pasted input more
        # than necessary.  We do this by trimming out the auto-indent initial
        # spaces, if the user's actual input started itself with whitespace.
        if self.autoindent:
            if num_ini_spaces(line) > self.indent_current_nsp:
                line = line[self.indent_current_nsp:]
                self.indent_current_nsp = 0
        
        return line

    #-------------------------------------------------------------------------
    # Methods to support auto-editing of SyntaxErrors.
    #-------------------------------------------------------------------------

    def edit_syntax_error(self):
        """The bottom half of the syntax error handler called in the main loop.

        Loop until syntax error is fixed or user cancels.
        """

        while self.SyntaxTB.last_syntax_error:
            # copy and clear last_syntax_error
            err = self.SyntaxTB.clear_err_state()
            if not self._should_recompile(err):
                return
            try:
                # may set last_syntax_error again if a SyntaxError is raised
                self.safe_execfile(err.filename,self.user_ns)
            except:
                self.showtraceback()
            else:
                try:
                    f = file(err.filename)
                    try:
                        # This should be inside a display_trap block and I 
                        # think it is.
                        sys.displayhook(f.read())
                    finally:
                        f.close()
                except:
                    self.showtraceback()

    def _should_recompile(self,e):
        """Utility routine for edit_syntax_error"""

        if e.filename in ('<ipython console>','<input>','<string>',
                          '<console>','<BackgroundJob compilation>',
                          None):
                              
            return False
        try:
            if (self.autoedit_syntax and 
                not self.ask_yes_no('Return to editor to correct syntax error? '
                              '[Y/n] ','y')):
                return False
        except EOFError:
            return False

        def int0(x):
            try:
                return int(x)
            except TypeError:
                return 0
        # always pass integer line and offset values to editor hook
        try:
            self.hooks.fix_error_editor(e.filename,
                int0(e.lineno),int0(e.offset),e.msg)
        except TryNext:
            warn('Could not open editor')
            return False
        return True

    #-------------------------------------------------------------------------
    # Things related to GUI support and pylab
    #-------------------------------------------------------------------------

    def enable_pylab(self, gui=None):
        """Activate pylab support at runtime.

        This turns on support for matplotlib, preloads into the interactive
        namespace all of numpy and pylab, and configures IPython to correcdtly
        interact with the GUI event loop.  The GUI backend to be used can be
        optionally selected with the optional :param:`gui` argument.

        Parameters
        ----------
        gui : optional, string

          If given, dictates the choice of matplotlib GUI backend to use
          (should be one of IPython's supported backends, 'tk', 'qt', 'wx' or
          'gtk'), otherwise we use the default chosen by matplotlib (as
          dictated by the matplotlib build-time options plus the user's
          matplotlibrc configuration file).
        """
        # We want to prevent the loading of pylab to pollute the user's
        # namespace as shown by the %who* magics, so we execute the activation
        # code in an empty namespace, and we update *both* user_ns and
        # user_ns_hidden with this information.
        ns = {}
        gui = pylab_activate(ns, gui)
        self.user_ns.update(ns)
        self.user_ns_hidden.update(ns)
        # Now we must activate the gui pylab wants to use, and fix %run to take
        # plot updates into account
        enable_gui(gui)
        self.magic_run = self._pylab_magic_run

    #-------------------------------------------------------------------------
    # Things related to exiting
    #-------------------------------------------------------------------------

    def ask_exit(self):
        """ Ask the shell to exit. Can be overiden and used as a callback. """
        self.exit_now = True

    def exit(self):
        """Handle interactive exit.

        This method calls the ask_exit callback."""
        if self.confirm_exit:
            if self.ask_yes_no('Do you really want to exit ([y]/n)?','y'):
                self.ask_exit()
        else:
            self.ask_exit()
            
    #------------------------------------------------------------------------
    # Magic overrides
    #------------------------------------------------------------------------
    # Once the base class stops inheriting from magic, this code needs to be
    # moved into a separate machinery as well.  For now, at least isolate here
    # the magics which this class needs to implement differently from the base
    # class, or that are unique to it.

    def magic_autoindent(self, parameter_s = ''):
        """Toggle autoindent on/off (if available)."""

        self.shell.set_autoindent()
        print "Automatic indentation is:",['OFF','ON'][self.shell.autoindent]

    @testdec.skip_doctest
    def magic_cpaste(self, parameter_s=''):
        """Paste & execute a pre-formatted code block from clipboard.
        
        You must terminate the block with '--' (two minus-signs) alone on the
        line. You can also provide your own sentinel with '%paste -s %%' ('%%' 
        is the new sentinel for this operation)
        
        The block is dedented prior to execution to enable execution of method
        definitions. '>' and '+' characters at the beginning of a line are
        ignored, to allow pasting directly from e-mails, diff files and
        doctests (the '...' continuation prompt is also stripped).  The
        executed block is also assigned to variable named 'pasted_block' for
        later editing with '%edit pasted_block'.
        
        You can also pass a variable name as an argument, e.g. '%cpaste foo'.
        This assigns the pasted block to variable 'foo' as string, without 
        dedenting or executing it (preceding >>> and + is still stripped)
        
        '%cpaste -r' re-executes the block previously entered by cpaste.
        
        Do not be alarmed by garbled output on Windows (it's a readline bug). 
        Just press enter and type -- (and press enter again) and the block 
        will be what was just pasted.
        
        IPython statements (magics, shell escapes) are not supported (yet).

        See also
        --------
        paste: automatically pull code from clipboard.
        
        Examples
        --------
        ::
        
          In [8]: %cpaste
          Pasting code; enter '--' alone on the line to stop.
          :>>> a = ["world!", "Hello"]
          :>>> print " ".join(sorted(a))
          :--
          Hello world!
        """
        
        opts,args = self.parse_options(parameter_s,'rs:',mode='string')
        par = args.strip()
        if opts.has_key('r'):
            self._rerun_pasted()
            return
        
        sentinel = opts.get('s','--')

        block = self._strip_pasted_lines_for_code(
            self._get_pasted_lines(sentinel))

        self._execute_block(block, par)

    def magic_paste(self, parameter_s=''):
        """Paste & execute a pre-formatted code block from clipboard.
        
        The text is pulled directly from the clipboard without user
        intervention and printed back on the screen before execution (unless
        the -q flag is given to force quiet mode).

        The block is dedented prior to execution to enable execution of method
        definitions. '>' and '+' characters at the beginning of a line are
        ignored, to allow pasting directly from e-mails, diff files and
        doctests (the '...' continuation prompt is also stripped).  The
        executed block is also assigned to variable named 'pasted_block' for
        later editing with '%edit pasted_block'.
        
        You can also pass a variable name as an argument, e.g. '%paste foo'.
        This assigns the pasted block to variable 'foo' as string, without 
        dedenting or executing it (preceding >>> and + is still stripped)

        Options
        -------
        
          -r: re-executes the block previously entered by cpaste.

          -q: quiet mode: do not echo the pasted text back to the terminal.
        
        IPython statements (magics, shell escapes) are not supported (yet).

        See also
        --------
        cpaste: manually paste code into terminal until you mark its end.
        """
        opts,args = self.parse_options(parameter_s,'rq',mode='string')
        par = args.strip()
        if opts.has_key('r'):
            self._rerun_pasted()
            return

        text = self.shell.hooks.clipboard_get()
        block = self._strip_pasted_lines_for_code(text.splitlines())

        # By default, echo back to terminal unless quiet mode is requested
        if not opts.has_key('q'):
            write = self.shell.write
            write(self.shell.pycolorize(block))
            if not block.endswith('\n'):
                write('\n')
            write("## -- End pasted text --\n")
            
        self._execute_block(block, par)


InteractiveShellABC.register(TerminalInteractiveShell)
