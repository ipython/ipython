# -*- coding: utf-8 -*-
"""Subclass of InteractiveShell for terminal based frontends."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de>
#  Copyright (C) 2001-2007 Fernando Perez. <fperez@colorado.edu>
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

import bdb
import os
import re
import sys
import textwrap

# We need to use nested to support python 2.6, once we move to >=2.7, we can
# use the with keyword's new builtin support for nested managers
try:
    from contextlib import nested
except:
    from IPython.utils.nested_context import nested

from IPython.core.error import TryNext, UsageError
from IPython.core.usage import interactive_usage, default_banner
from IPython.core.inputsplitter import IPythonInputSplitter
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.encoding import get_stream_enc
from IPython.utils import py3compat
from IPython.utils.terminal import toggle_set_term_title, set_term_title
from IPython.utils.process import abbrev_cwd
from IPython.utils.warn import warn, error
from IPython.utils.text import num_ini_spaces, SList, strip_email_quotes
from IPython.utils.traitlets import Integer, CBool, Unicode

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


def get_pasted_lines(sentinel, l_input=py3compat.input):
    """ Yield pasted lines until the user enters the given sentinel value.
    """
    print("Pasting code; enter '%s' alone on the line to stop or use Ctrl-D." \
          % sentinel)
    while True:
        try:
            l = l_input(':')
            if l == sentinel:
                return
            else:
                yield l
        except EOFError:
            print('<EOF>')
            return


#------------------------------------------------------------------------
# Terminal-specific magics
#------------------------------------------------------------------------

@magics_class
class TerminalMagics(Magics):
    def __init__(self, shell):
        super(TerminalMagics, self).__init__(shell)
        self.input_splitter = IPythonInputSplitter(input_mode='line')

    def cleanup_input(self, block):
        """Apply all possible IPython cleanups to an input block.

        This means:

        - remove any global leading whitespace (dedent)
        - remove any email quotes ('>') if they are present in *all* lines
        - apply all static inputsplitter transforms and break into sub-blocks
        - apply prefilter() to each sub-block that is a single line.

        Parameters
        ----------
        block : str
          A possibly multiline input string of code.

        Returns
        -------
        transformed block : str
          The input, with all transformations above applied.
        """
        # We have to effectively implement client-side the loop that is done by
        # the terminal frontend, and furthermore do it on a block that can
        # possibly contain multiple statments pasted in one go.

        # First, run the input through the block splitting code.  We should
        # eventually make this a self-contained method in the inputsplitter.
        isp = self.input_splitter
        isp.reset()
        b = textwrap.dedent(block)

        # Remove email quotes first.  These must be consistently applied to
        # *all* lines to be removed
        b = strip_email_quotes(b)

        # Split the input into independent sub-blocks so we can later do
        # prefiltering (which must be done *only* to single-line inputs)
        blocks = []
        last_block = []
        for line in b.splitlines():
            isp.push(line)
            last_block.append(line)
            if not isp.push_accepts_more():
                blocks.append(isp.source_reset())
                last_block = []
        if last_block:
            blocks.append('\n'.join(last_block))

        # Now, apply prefiltering to any one-line block to match the behavior
        # of the interactive terminal
        final_blocks = []
        for block in blocks:
            lines = block.splitlines()
            if len(lines) == 1:
                final_blocks.append(self.shell.prefilter(lines[0]))
            else:
                final_blocks.append(block)

        # We now have the final version of the input code as a list of blocks,
        # with all inputsplitter transformations applied and single-line blocks
        # run through prefilter.  For further processing, turn into a single
        # string as the rest of our apis use string inputs.
        return '\n'.join(final_blocks)
        
    def store_or_execute(self, block, name):
        """ Execute a block, or store it in a variable, per the user's request.
        """

        b = self.cleanup_input(block)
        if name:
            # If storing it for further editing
            self.shell.user_ns[name] = SList(b.splitlines())
            print("Block assigned to '%s'" % name)
        else:
            self.shell.user_ns['pasted_block'] = b
            self.shell.using_paste_magics = True
            try:
                self.shell.run_cell(b)
            finally:
                self.shell.using_paste_magics = False

    def rerun_pasted(self, name='pasted_block'):
        """ Rerun a previously pasted command.
        """
        b = self.shell.user_ns.get(name)

        # Sanity checks
        if b is None:
            raise UsageError('No previous pasted block available')
        if not isinstance(b, basestring):
            raise UsageError(
                "Variable 'pasted_block' is not a string, can't execute")

        print("Re-executing '%s...' (%d chars)"% (b.split('\n',1)[0], len(b)))
        self.shell.run_cell(b)

    @line_magic
    def autoindent(self, parameter_s = ''):
        """Toggle autoindent on/off (if available)."""

        self.shell.set_autoindent()
        print("Automatic indentation is:",['OFF','ON'][self.shell.autoindent])

    @skip_doctest
    @line_magic
    def cpaste(self, parameter_s=''):
        """Paste & execute a pre-formatted code block from clipboard.

        You must terminate the block with '--' (two minus-signs) or Ctrl-D
        alone on the line. You can also provide your own sentinel with '%paste
        -s %%' ('%%' is the new sentinel for this operation)

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
        opts, name = self.parse_options(parameter_s, 'rs:', mode='string')
        if 'r' in opts:
            self.rerun_pasted()
            return

        sentinel = opts.get('s', '--')
        block = '\n'.join(get_pasted_lines(sentinel))
        self.store_or_execute(block, name)

    @line_magic
    def paste(self, parameter_s=''):
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
        executing it (preceding >>> and + is still stripped).

        Options
        -------

          -r: re-executes the block previously entered by cpaste.

          -q: quiet mode: do not echo the pasted text back to the terminal.

        IPython statements (magics, shell escapes) are not supported (yet).

        See also
        --------
        cpaste: manually paste code into terminal until you mark its end.
        """
        opts, name = self.parse_options(parameter_s, 'rq', mode='string')
        if 'r' in opts:
            self.rerun_pasted()
            return
        try:
            block = self.shell.hooks.clipboard_get()
        except TryNext as clipboard_exc:
            message = getattr(clipboard_exc, 'args')
            if message:
                error(message[0])
            else:
                error('Could not get text from the clipboard.')
            return

        # By default, echo back to terminal unless quiet mode is requested
        if 'q' not in opts:
            write = self.shell.write
            write(self.shell.pycolorize(block))
            if not block.endswith('\n'):
                write('\n')
            write("## -- End pasted text --\n")

        self.store_or_execute(block, name)

    # Class-level: add a '%cls' magic only on Windows
    if sys.platform == 'win32':
        @line_magic
        def cls(self, s):
            """Clear screen.
            """
            os.system("cls")

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

    screen_length = Integer(0, config=True,
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
    
    # This `using_paste_magics` is used to detect whether the code is being
    # executed via paste magics functions
    using_paste_magics = CBool(False)

    # In the terminal, GUI control is done via PyOS_InputHook
    def enable_gui(gui=None, app=None):
        """Switch amongst GUI input hooks by name.
        """
        # Deferred import
        from IPython.lib.inputhook import enable_gui as real_enable_gui
        return real_enable_gui(gui, app)
    
    def __init__(self, config=None, ipython_dir=None, profile_dir=None,
                 user_ns=None, user_module=None, custom_exceptions=((),None),
                 usage=None, banner1=None, banner2=None, display_banner=None):

        super(TerminalInteractiveShell, self).__init__(
            config=config, ipython_dir=ipython_dir, profile_dir=profile_dir, user_ns=user_ns,
            user_module=user_module, custom_exceptions=custom_exceptions
        )
        # use os.system instead of utils.process.system by default,
        # because piped system doesn't make sense in the Terminal:
        self.system = self.system_raw

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
        if self.profile and self.profile != 'default':
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

    def _replace_rlhist_multiline(self, source_raw, hlen_before_cell):
        """Store multiple lines as a single entry in history"""

        # do nothing without readline or disabled multiline
        if not self.has_readline or not self.multiline_history:
            return hlen_before_cell

        # windows rl has no remove_history_item
        if not hasattr(self.readline, "remove_history_item"):
            return hlen_before_cell

        # skip empty cells
        if not source_raw.rstrip():
            return hlen_before_cell

        # nothing changed do nothing, e.g. when rl removes consecutive dups
        hlen = self.readline.get_current_history_length()
        if hlen == hlen_before_cell:
            return hlen_before_cell

        for i in range(hlen - hlen_before_cell):
            self.readline.remove_history_item(hlen - i - 1)
        stdin_encoding = get_stream_enc(sys.stdin, 'utf-8')
        self.readline.add_history(py3compat.unicode_to_str(source_raw.rstrip(),
                                    stdin_encoding))
        return self.readline.get_current_history_length()

    def interact(self, display_banner=None):
        """Closely emulate the interactive Python console."""

        # batch run -> do not interact
        if self.exit_now:
            return

        if display_banner is None:
            display_banner = self.display_banner

        if isinstance(display_banner, basestring):
            self.show_banner(display_banner)
        elif display_banner:
            self.show_banner()

        more = False

        if self.has_readline:
            self.readline_startup_hook(self.pre_readline)
            hlen_b4_cell = self.readline.get_current_history_length()
        else:
            hlen_b4_cell = 0
        # exit_now is set by a call to %Exit or %Quit, through the
        # ask_exit callback.

        while not self.exit_now:
            self.hooks.pre_prompt_hook()
            if more:
                try:
                    prompt = self.prompt_manager.render('in2')
                except:
                    self.showtraceback()
                if self.autoindent:
                    self.rl_do_indent = True

            else:
                try:
                    prompt = self.separate_in + self.prompt_manager.render('in')
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
                    source_raw = self.input_splitter.source_raw_reset()[1]
                    hlen_b4_cell = \
                        self._replace_rlhist_multiline(source_raw, hlen_b4_cell)
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
                    self.run_cell(source_raw, store_history=True)
                    hlen_b4_cell = \
                        self._replace_rlhist_multiline(source_raw, hlen_b4_cell)

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
        
        # raw_input expects str, but we pass it unicode sometimes
        prompt = py3compat.cast_bytes_py2(prompt)

        try:
            line = py3compat.str_to_unicode(self.raw_input_original(prompt))
        except ValueError:
            warn("\n********\nYou or a %run:ed script called sys.stdin.close()"
                 " or sys.stdout.close()!\nExiting IPython!\n")
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
                    f = open(err.filename)
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

    #-------------------------------------------------------------------------
    # Things related to magics
    #-------------------------------------------------------------------------

    def init_magics(self):
        super(TerminalInteractiveShell, self).init_magics()
        self.register_magics(TerminalMagics)

    def showindentationerror(self):
        super(TerminalInteractiveShell, self).showindentationerror()
        if not self.using_paste_magics:
            print("If you want to paste code into IPython, try the "
                "%paste and %cpaste magic functions.")


InteractiveShellABC.register(TerminalInteractiveShell)
