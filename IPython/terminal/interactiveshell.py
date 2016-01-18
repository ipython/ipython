# -*- coding: utf-8 -*-
"""Subclass of InteractiveShell for terminal based frontends."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import bdb
import os
import sys

from IPython.core.error import TryNext, UsageError
from IPython.core.usage import interactive_usage
from IPython.core.inputsplitter import IPythonInputSplitter, ESC_MAGIC
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.lib.clipboard import ClipboardEmpty
from IPython.utils.contexts import NoOpContext
from IPython.utils.decorators import undoc
from IPython.utils.encoding import get_stream_enc
from IPython.utils import py3compat
from IPython.utils.terminal import toggle_set_term_title, set_term_title
from IPython.utils.process import abbrev_cwd
from IPython.utils.warn import warn, error
from IPython.utils.text import num_ini_spaces, SList, strip_email_quotes
from traitlets import Integer, CBool, Unicode


def get_default_editor():
    try:
        ed = os.environ['EDITOR']
        if not py3compat.PY3:
            ed = ed.decode()
        return ed
    except KeyError:
        pass
    except UnicodeError:
        warn("$EDITOR environment variable is not pure ASCII. Using platform "
             "default editor.")

    if os.name == 'posix':
        return 'vi'  # the only one guaranteed to be there!
    else:
        return 'notepad' # same in Windows!

def get_pasted_lines(sentinel, l_input=py3compat.input, quiet=False):
    """ Yield pasted lines until the user enters the given sentinel value.
    """
    if not quiet:
        print("Pasting code; enter '%s' alone on the line to stop or use Ctrl-D." \
              % sentinel)
        prompt = ":"
    else:
        prompt = ""
    while True:
        try:
            l = py3compat.str_to_unicode(l_input(prompt))
            if l == sentinel:
                return
            else:
                yield l
        except EOFError:
            print('<EOF>')
            return

@undoc
def no_op(*a, **kw): pass


class ReadlineNoRecord(object):
    """Context manager to execute some code, then reload readline history
    so that interactive input to the code doesn't appear when pressing up."""
    def __init__(self, shell):
        self.shell = shell
        self._nested_level = 0

    def __enter__(self):
        if self._nested_level == 0:
            try:
                self.orig_length = self.current_length()
                self.readline_tail = self.get_readline_tail()
            except (AttributeError, IndexError):   # Can fail with pyreadline
                self.orig_length, self.readline_tail = 999999, []
        self._nested_level += 1

    def __exit__(self, type, value, traceback):
        self._nested_level -= 1
        if self._nested_level == 0:
            # Try clipping the end if it's got longer
            try:
                e = self.current_length() - self.orig_length
                if e > 0:
                    for _ in range(e):
                        self.shell.readline.remove_history_item(self.orig_length)

                # If it still doesn't match, just reload readline history.
                if self.current_length() != self.orig_length \
                    or self.get_readline_tail() != self.readline_tail:
                    self.shell.refill_readline_hist()
            except (AttributeError, IndexError):
                pass
        # Returning False will cause exceptions to propagate
        return False

    def current_length(self):
        return self.shell.readline.get_current_history_length()

    def get_readline_tail(self, n=10):
        """Get the last n items in readline history."""
        end = self.shell.readline.get_current_history_length() + 1
        start = max(end-n, 1)
        ghi = self.shell.readline.get_history_item
        return [ghi(x) for x in range(start, end)]


@magics_class
class TerminalMagics(Magics):
    def __init__(self, shell):
        super(TerminalMagics, self).__init__(shell)
        self.input_splitter = IPythonInputSplitter()
        
    def store_or_execute(self, block, name):
        """ Execute a block, or store it in a variable, per the user's request.
        """
        if name:
            # If storing it for further editing
            self.shell.user_ns[name] = SList(block.splitlines())
            print("Block assigned to '%s'" % name)
        else:
            b = self.preclean_input(block)
            self.shell.user_ns['pasted_block'] = b
            self.shell.using_paste_magics = True
            try:
                self.shell.run_cell(b)
            finally:
                self.shell.using_paste_magics = False
    
    def preclean_input(self, block):
        lines = block.splitlines()
        while lines and not lines[0].strip():
            lines = lines[1:]
        return strip_email_quotes('\n'.join(lines))

    def rerun_pasted(self, name='pasted_block'):
        """ Rerun a previously pasted command.
        """
        b = self.shell.user_ns.get(name)

        # Sanity checks
        if b is None:
            raise UsageError('No previous pasted block available')
        if not isinstance(b, py3compat.string_types):
            raise UsageError(
                "Variable 'pasted_block' is not a string, can't execute")

        print("Re-executing '%s...' (%d chars)"% (b.split('\n',1)[0], len(b)))
        self.shell.run_cell(b)

    @line_magic
    def autoindent(self, parameter_s = ''):
        """Toggle autoindent on/off (if available)."""

        self.shell.set_autoindent()
        print("Automatic indentation is:",['OFF','ON'][self.shell.autoindent])

    @line_magic
    def cpaste(self, parameter_s=''):
        """Paste & execute a pre-formatted code block from clipboard.

        You must terminate the block with '--' (two minus-signs) or Ctrl-D
        alone on the line. You can also provide your own sentinel with '%paste
        -s %%' ('%%' is the new sentinel for this operation).

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
        '%cpaste -q' suppresses any additional output messages.

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
        opts, name = self.parse_options(parameter_s, 'rqs:', mode='string')
        if 'r' in opts:
            self.rerun_pasted()
            return

        quiet = ('q' in opts)

        sentinel = opts.get('s', u'--')
        block = '\n'.join(get_pasted_lines(sentinel, quiet=quiet))
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

        Options:

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
        except ClipboardEmpty:
            raise UsageError("The clipboard appears to be empty")

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


class TerminalInteractiveShell(InteractiveShell):

    autoedit_syntax = CBool(False, config=True,
        help="auto editing of files with syntax errors.")
    confirm_exit = CBool(True, config=True,
        help="""
        Set to confirm when you try to exit IPython with an EOF (Control-D
        in Unix, Control-Z/Enter in Windows). By typing 'exit' or 'quit',
        you can force a direct exit without any confirmation.""",
    )
    # This display_banner only controls whether or not self.show_banner()
    # is called when mainloop/interact are called.  The default is False
    # because for the terminal based application, the banner behavior
    # is controlled by the application.
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
    usage = Unicode(interactive_usage)
    
    # This `using_paste_magics` is used to detect whether the code is being
    # executed via paste magics functions
    using_paste_magics = CBool(False)

    # In the terminal, GUI control is done via PyOS_InputHook
    @staticmethod
    def enable_gui(gui=None, app=None):
        """Switch amongst GUI input hooks by name.
        """
        # Deferred import
        from IPython.lib.inputhook import enable_gui as real_enable_gui
        try:
            return real_enable_gui(gui, app)
        except ValueError as e:
            raise UsageError("%s" % e)
    
    system = InteractiveShell.system_raw

    #-------------------------------------------------------------------------
    # Overrides of init stages
    #-------------------------------------------------------------------------

    def init_display_formatter(self):
        super(TerminalInteractiveShell, self).init_display_formatter()
        # terminal only supports plaintext
        self.display_formatter.active_types = ['text/plain']

    #-------------------------------------------------------------------------
    # Things related to readline
    #-------------------------------------------------------------------------

    def init_readline(self):
        """Command history completion/saving/reloading."""

        if self.readline_use:
            import IPython.utils.rlineimpl as readline

        self.rl_next_input = None
        self.rl_do_indent = False

        if not self.readline_use or not readline.have_readline:
            self.readline = None
            # Set a number of methods that depend on readline to be no-op
            self.readline_no_record = NoOpContext()
            self.set_readline_completer = no_op
            self.set_custom_completer = no_op
            if self.readline_use:
                warn('Readline services not available or not loaded.')
        else:
            self.has_readline = True
            self.readline = readline
            sys.modules['readline'] = readline

            # Platform-specific configuration
            if os.name == 'nt':
                # FIXME - check with Frederick to see if we can harmonize
                # naming conventions with pyreadline to avoid this
                # platform-dependent check
                self.readline_startup_hook = readline.set_pre_input_hook
            else:
                self.readline_startup_hook = readline.set_startup_hook

            # Readline config order:
            # - IPython config (default value)
            # - custom inputrc
            # - IPython config (user customized)

            # load IPython config before inputrc if default
            # skip if libedit because parse_and_bind syntax is different
            if not self._custom_readline_config and not readline.uses_libedit:
                for rlcommand in self.readline_parse_and_bind:
                    readline.parse_and_bind(rlcommand)

            # Load user's initrc file (readline config)
            # Or if libedit is used, load editrc.
            inputrc_name = os.environ.get('INPUTRC')
            if inputrc_name is None:
                inputrc_name = '.inputrc'
                if readline.uses_libedit:
                    inputrc_name = '.editrc'
                inputrc_name = os.path.join(self.home_dir, inputrc_name)
            if os.path.isfile(inputrc_name):
                try:
                    readline.read_init_file(inputrc_name)
                except:
                    warn('Problems reading readline initialization file <%s>'
                         % inputrc_name)

            # load IPython config after inputrc if user has customized
            if self._custom_readline_config:
                for rlcommand in self.readline_parse_and_bind:
                    readline.parse_and_bind(rlcommand)

            # Remove some chars from the delimiters list.  If we encounter
            # unicode chars, discard them.
            delims = readline.get_completer_delims()
            if not py3compat.PY3:
                delims = delims.encode("ascii", "ignore")
            for d in self.readline_remove_delims:
                delims = delims.replace(d, "")
            delims = delims.replace(ESC_MAGIC, '')
            readline.set_completer_delims(delims)
            # Store these so we can restore them if something like rpy2 modifies
            # them.
            self.readline_delims = delims
            # otherwise we end up with a monster history after a while:
            readline.set_history_length(self.history_length)

            self.refill_readline_hist()
            self.readline_no_record = ReadlineNoRecord(self)

        # Configure auto-indent for all platforms
        self.set_autoindent(self.autoindent)

    def init_completer(self):
        super(TerminalInteractiveShell, self).init_completer()

        # Only configure readline if we truly are using readline.
        if self.has_readline:
            self.set_readline_completer()

    def set_readline_completer(self):
        """Reset readline's completer to be our own."""
        self.readline.set_completer(self.Completer.rlcomplete)


    def pre_readline(self):
        """readline hook to be used at the start of each line.

        It handles auto-indent and text from set_next_input."""

        if self.rl_do_indent:
            self.readline.insert_text(self._indent_current_str())
        if self.rl_next_input is not None:
            self.readline.insert_text(self.rl_next_input)
            self.rl_next_input = None

    def refill_readline_hist(self):
        # Load the last 1000 lines from history
        self.readline.clear_history()
        stdin_encoding = sys.stdin.encoding or "utf-8"
        last_cell = u""
        for _, _, cell in self.history_manager.get_tail(self.history_load_length,
                                                        include_latest=True):
            # Ignore blank lines and consecutive duplicates
            cell = cell.rstrip()
            if cell and (cell != last_cell):
                try:
                    if self.multiline_history:
                          self.readline.add_history(py3compat.unicode_to_str(cell,
                                                                    stdin_encoding))
                    else:
                        for line in cell.splitlines():
                            self.readline.add_history(py3compat.unicode_to_str(line,
                                                                    stdin_encoding))
                    last_cell = cell

                except TypeError:
                    # The history DB can get corrupted so it returns strings
                    # containing null bytes, which readline objects to.
                    continue

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

    def _term_title_changed(self, name, new_value):
        self.init_term_title()

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
        else :
            aliases = []

        for name, cmd in aliases:
            self.alias_manager.soft_define_alias(name, cmd)

    #-------------------------------------------------------------------------
    # Mainloop and code execution logic
    #-------------------------------------------------------------------------

    def mainloop(self, display_banner=None):
        """Start the mainloop.

        If an optional banner argument is given, it will override the
        internally created default banner.
        """

        with self.builtin_trap, self.display_trap:

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

        if isinstance(display_banner, py3compat.string_types):
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
                    self.write('\n' + self.get_exception_only())
                    source_raw = self.input_splitter.raw_reset()
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
                try:
                    self.input_splitter.push(line)
                    more = self.input_splitter.push_accepts_more()
                except SyntaxError:
                    # Run the code directly - run_cell takes care of displaying
                    # the exception.
                    more = False
                if (self.SyntaxTB.last_syntax_error and
                    self.autoedit_syntax):
                    self.edit_syntax_error()
                if not more:
                    source_raw = self.input_splitter.raw_reset()
                    self.run_cell(source_raw, store_history=True)
                    hlen_b4_cell = \
                        self._replace_rlhist_multiline(source_raw, hlen_b4_cell)

        # Turn off the exit flag, so the mainloop can be restarted if desired
        self.exit_now = False

    def raw_input(self, prompt=''):
        """Write a prompt and read a line.

        The returned line does not include the trailing newline.
        When the user enters the EOF key sequence, EOFError is raised.

        Parameters
        ----------

        prompt : str, optional
          A string to be printed to prompt the user.
        """
        # raw_input expects str, but we pass it unicode sometimes
        prompt = py3compat.cast_bytes_py2(prompt)

        try:
            line = py3compat.cast_unicode_py2(self.raw_input_original(prompt))
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
            if self.ask_yes_no('Do you really want to exit ([y]/n)?','y','n'):
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
