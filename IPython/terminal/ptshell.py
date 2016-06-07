"""IPython terminal interface using prompt_toolkit in place of readline"""
from __future__ import print_function

import os
import sys
import signal
from warnings import warn

from IPython.core.error import TryNext
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.utils.py3compat import PY3, cast_unicode_py2, input
from IPython.utils.terminal import toggle_set_term_title, set_term_title
from IPython.utils.process import abbrev_cwd
from traitlets import Bool, Unicode, Dict, Integer, observe, Instance, Type

from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER, EditingMode
from prompt_toolkit.filters import HasFocus, HasSelection, Condition, ViInsertMode, EmacsInsertMode, IsDone
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import create_prompt_application, create_eventloop, create_prompt_layout
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.processors import ConditionalProcessor, HighlightMatchingBracketProcessor
from prompt_toolkit.styles import PygmentsStyle, DynamicStyle

from pygments.styles import get_style_by_name, get_all_styles
from pygments.token import Token

from .debugger import TerminalPdb, Pdb
from .magics import TerminalMagics
from .pt_inputhooks import get_inputhook_func
from .prompts import Prompts, ClassicPrompts, RichPromptDisplayHook
from .ptutils import IPythonPTCompleter, IPythonPTLexer


def get_default_editor():
    try:
        ed = os.environ['EDITOR']
        if not PY3:
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


if sys.stdin and sys.stdout and sys.stderr:
    _is_tty = (sys.stdin.isatty()) and (sys.stdout.isatty()) and  (sys.stderr.isatty())
else:
    _is_tty = False


_use_simple_prompt = ('IPY_TEST_SIMPLE_PROMPT' in os.environ) or (not _is_tty)

class TerminalInteractiveShell(InteractiveShell):
    colors_force = True

    space_for_menu = Integer(6, help='Number of line at the bottom of the screen '
                                                  'to reserve for the completion menu'
                            ).tag(config=True)

    def _space_for_menu_changed(self, old, new):
        self._update_layout()

    pt_cli = None
    debugger_history = None

    simple_prompt = Bool(_use_simple_prompt,
        help="""Use `raw_input` for the REPL, without completion, multiline input, and prompt colors.

            Useful when controlling IPython as a subprocess, and piping STDIN/OUT/ERR. Known usage are:
            IPython own testing machinery, and emacs inferior-shell integration through elpy.

            This mode default to `True` if the `IPY_TEST_SIMPLE_PROMPT`
            environment variable is set, or the current terminal is not a tty.

            """
            ).tag(config=True)

    @property
    def debugger_cls(self):
        return Pdb if self.simple_prompt else TerminalPdb

    autoedit_syntax = Bool(False,
        help="auto editing of files with syntax errors.",
    ).tag(config=True)


    confirm_exit = Bool(True,
        help="""
        Set to confirm when you try to exit IPython with an EOF (Control-D
        in Unix, Control-Z/Enter in Windows). By typing 'exit' or 'quit',
        you can force a direct exit without any confirmation.""",
    ).tag(config=True)

    editing_mode = Unicode('emacs',
        help="Shortcut style to use at the prompt. 'vi' or 'emacs'.",
    ).tag(config=True)

    mouse_support = Bool(False,
        help="Enable mouse support in the prompt"
    ).tag(config=True)

    highlighting_style = Unicode('default',
            help="The name of a Pygments style to use for syntax highlighting: \n %s" % ', '.join(get_all_styles())
    ).tag(config=True)

    
    @observe('highlighting_style')
    def _highlighting_style_changed(self, change):
        self._style = self._make_style_from_name(self.highlighting_style)

    highlighting_style_overrides = Dict(
        help="Override highlighting format for specific tokens"
    ).tag(config=True)

    editor = Unicode(get_default_editor(),
        help="Set the editor used by IPython (default to $EDITOR/vi/notepad)."
    ).tag(config=True)

    prompts_class = Type(Prompts, config=True, help='Class used to generate Prompt token for prompt_toolkit')

    prompts = Instance(Prompts)

    def _prompts_default(self):
        return self.prompts_class(self)

    @observe('prompts')
    def _(self, change):
        self._update_layout()

    def _displayhook_class_default(self):
        return RichPromptDisplayHook

    term_title = Bool(True,
        help="Automatically set the terminal title"
    ).tag(config=True)

    display_completions_in_columns = Bool(False,
        help="Display a multi column completion menu.",
    ).tag(config=True)

    highlight_matching_brackets = Bool(True,
        help="Highlight matching brackets .",
    ).tag(config=True)

    @observe('term_title')
    def init_term_title(self, change=None):
        # Enable or disable the terminal title.
        if self.term_title:
            toggle_set_term_title(True)
            set_term_title('IPython: ' + abbrev_cwd())
        else:
            toggle_set_term_title(False)

    def init_prompt_toolkit_cli(self):
        self._app = None
        if self.simple_prompt:
            # Fall back to plain non-interactive output for tests.
            # This is very limited, and only accepts a single line.
            def prompt():
                return cast_unicode_py2(input('In [%d]: ' % self.execution_count))
            self.prompt_for_code = prompt
            return

        kbmanager = KeyBindingManager.for_prompt()
        insert_mode = ViInsertMode() | EmacsInsertMode()
        # Ctrl+J == Enter, seemingly
        @kbmanager.registry.add_binding(Keys.ControlJ,
                            filter=(HasFocus(DEFAULT_BUFFER)
                                    & ~HasSelection()
                                    & insert_mode
                                   ))
        def _(event):
            b = event.current_buffer
            d = b.document

            if b.complete_state:
                cs = b.complete_state
                b.apply_completion(cs.current_completion)
                return

            if not (d.on_last_line or d.cursor_position_row >= d.line_count
                                           - d.empty_line_count_at_the_end()):
                b.newline()
                return

            status, indent = self.input_splitter.check_complete(d.text)

            if (status != 'incomplete') and b.accept_action.is_returnable:
                b.accept_action.validate_and_handle(event.cli, b)
            else:
                b.insert_text('\n' + (' ' * (indent or 0)))

        @kbmanager.registry.add_binding(Keys.ControlC, filter=HasFocus(DEFAULT_BUFFER))
        def _reset_buffer(event):
            event.current_buffer.reset()

        @kbmanager.registry.add_binding(Keys.ControlC, filter=HasFocus(SEARCH_BUFFER))
        def _reset_search_buffer(event):
            if event.current_buffer.document.text:
                event.current_buffer.reset()
            else:
                event.cli.push_focus(DEFAULT_BUFFER)

        supports_suspend = Condition(lambda cli: hasattr(signal, 'SIGTSTP'))

        @kbmanager.registry.add_binding(Keys.ControlZ, filter=supports_suspend)
        def _suspend_to_bg(event):
            event.cli.suspend_to_background()

        @Condition
        def cursor_in_leading_ws(cli):
            before = cli.application.buffer.document.current_line_before_cursor
            return (not before) or before.isspace()

        # Ctrl+I == Tab
        @kbmanager.registry.add_binding(Keys.ControlI,
                            filter=(HasFocus(DEFAULT_BUFFER)
                                    & ~HasSelection()
                                    & insert_mode
                                    & cursor_in_leading_ws
                                   ))
        def _indent_buffer(event):
            event.current_buffer.insert_text(' ' * 4)

        # Pre-populate history from IPython's history database
        history = InMemoryHistory()
        last_cell = u""
        for __, ___, cell in self.history_manager.get_tail(self.history_load_length,
                                                        include_latest=True):
            # Ignore blank lines and consecutive duplicates
            cell = cell.rstrip()
            if cell and (cell != last_cell):
                history.append(cell)

        self._style = self._make_style_from_name(self.highlighting_style)
        style = DynamicStyle(lambda: self._style)

        editing_mode = getattr(EditingMode, self.editing_mode.upper())

        self._app = create_prompt_application(
                            editing_mode=editing_mode,
                            key_bindings_registry=kbmanager.registry,
                            history=history,
                            completer=IPythonPTCompleter(self.Completer),
                            enable_history_search=True,
                            style=style,
                            mouse_support=self.mouse_support,
                            **self._layout_options()
        )
        self._eventloop = create_eventloop(self.inputhook)
        self.pt_cli = CommandLineInterface(self._app, eventloop=self._eventloop)

    def _make_style_from_name(self, name):
        """
        Small wrapper that make an IPython compatible style from a style name

        We need that to add style for prompt ... etc. 
        """
        style_cls = get_style_by_name(name)
        style_overrides = {
            Token.Prompt: '#009900',
            Token.PromptNum: '#00ff00 bold',
            Token.OutPrompt: '#990000',
            Token.OutPromptNum: '#ff0000 bold',
        }
        if name == 'default':
            style_cls = get_style_by_name('default')
            # The default theme needs to be visible on both a dark background
            # and a light background, because we can't tell what the terminal
            # looks like. These tweaks to the default theme help with that.
            style_overrides.update({
                Token.Number: '#007700',
                Token.Operator: 'noinherit',
                Token.String: '#BB6622',
                Token.Name.Function: '#2080D0',
                Token.Name.Class: 'bold #2080D0',
                Token.Name.Namespace: 'bold #2080D0',
            })
        style_overrides.update(self.highlighting_style_overrides)
        style = PygmentsStyle.from_defaults(pygments_style_cls=style_cls,
                                            style_dict=style_overrides)

        return style

    def _layout_options(self):
        """
        Return the current layout option for the current Terminal InteractiveShell
        """
        return {
                'lexer':IPythonPTLexer(),
                'reserve_space_for_menu':self.space_for_menu,
                'get_prompt_tokens':self.prompts.in_prompt_tokens,
                'get_continuation_tokens':self.prompts.continuation_prompt_tokens,
                'multiline':True,
                'display_completions_in_columns': self.display_completions_in_columns,

                # Highlight matching brackets, but only when this setting is
                # enabled, and only when the DEFAULT_BUFFER has the focus.
                'extra_input_processors': [ConditionalProcessor(
                        processor=HighlightMatchingBracketProcessor(chars='[](){}'),
                        filter=HasFocus(DEFAULT_BUFFER) & ~IsDone() &
                            Condition(lambda cli: self.highlight_matching_brackets))],
                }

    def _update_layout(self):
        """
        Ask for a re computation of the application layout, if for example ,
        some configuration options have changed.
        """
        if getattr(self, '._app', None):
            self._app.layout = create_prompt_layout(**self._layout_options())

    def prompt_for_code(self):
        document = self.pt_cli.run(
            pre_run=self.pre_prompt, reset_current_buffer=True)
        return document.text

    def init_io(self):
        if sys.platform not in {'win32', 'cli'}:
            return

        import colorama
        colorama.init()

        # For some reason we make these wrappers around stdout/stderr.
        # For now, we need to reset them so all output gets coloured.
        # https://github.com/ipython/ipython/issues/8669
        from IPython.utils import io
        io.stdout = io.IOStream(sys.stdout)
        io.stderr = io.IOStream(sys.stderr)

    def init_magics(self):
        super(TerminalInteractiveShell, self).init_magics()
        self.register_magics(TerminalMagics)

    def init_alias(self):
        # The parent class defines aliases that can be safely used with any
        # frontend.
        super(TerminalInteractiveShell, self).init_alias()

        # Now define aliases that only make sense on the terminal, because they
        # need direct access to the console in a way that we can't emulate in
        # GUI or web frontend
        if os.name == 'posix':
            for cmd in ['clear', 'more', 'less', 'man']:
                self.alias_manager.soft_define_alias(cmd, cmd)


    def __init__(self, *args, **kwargs):
        super(TerminalInteractiveShell, self).__init__(*args, **kwargs)
        self.init_prompt_toolkit_cli()
        self.init_term_title()
        self.keep_running = True

        self.debugger_history = InMemoryHistory()

    def ask_exit(self):
        self.keep_running = False

    rl_next_input = None

    def pre_prompt(self):
        if self.rl_next_input:
            self.pt_cli.application.buffer.text = cast_unicode_py2(self.rl_next_input)
            self.rl_next_input = None

    def interact(self):
        while self.keep_running:
            print(self.separate_in, end='')

            try:
                code = self.prompt_for_code()
            except EOFError:
                if (not self.confirm_exit) \
                        or self.ask_yes_no('Do you really want to exit ([y]/n)?','y','n'):
                    self.ask_exit()

            else:
                if code:
                    self.run_cell(code, store_history=True)
                    if self.autoedit_syntax and self.SyntaxTB.last_syntax_error:
                        self.edit_syntax_error()

    def mainloop(self):
        # An extra layer of protection in case someone mashing Ctrl-C breaks
        # out of our internal code.
        while True:
            try:
                self.interact()
                break
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt escaped interact()\n")
        
        if hasattr(self, '_eventloop'):
            self._eventloop.close()

    _inputhook = None
    def inputhook(self, context):
        if self._inputhook is not None:
            self._inputhook(context)

    def enable_gui(self, gui=None):
        if gui:
            self._inputhook = get_inputhook_func(gui)
        else:
            self._inputhook = None

    # Methods to support auto-editing of SyntaxErrors:

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
                self.safe_execfile(err.filename, self.user_ns)
            except:
                self.showtraceback()
            else:
                try:
                    with open(err.filename) as f:
                        # This should be inside a display_trap block and I
                        # think it is.
                        sys.displayhook(f.read())
                except:
                    self.showtraceback()

    def _should_recompile(self, e):
        """Utility routine for edit_syntax_error"""

        if e.filename in ('<ipython console>', '<input>', '<string>',
                          '<console>', '<BackgroundJob compilation>',
                          None):
            return False
        try:
            if (self.autoedit_syntax and
                    not self.ask_yes_no(
                        'Return to editor to correct syntax error? '
                        '[Y/n] ', 'y')):
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
                                        int0(e.lineno), int0(e.offset),
                                        e.msg)
        except TryNext:
            warn('Could not open editor')
            return False
        return True

    # Run !system commands directly, not through pipes, so terminal programs
    # work correctly.
    system = InteractiveShell.system_raw

    def auto_rewrite_input(self, cmd):
        """Overridden from the parent class to use fancy rewriting prompt"""
        if not self.show_rewritten_input:
            return

        tokens = self.prompts.rewrite_prompt_tokens()
        if self.pt_cli:
            self.pt_cli.print_tokens(tokens)
            print(cmd)
        else:
            prompt = ''.join(s for t, s in tokens)
            print(prompt, cmd, sep='')

    _prompts_before = None
    def switch_doctest_mode(self, mode):
        """Switch prompts to classic for %doctest_mode"""
        if mode:
            self._prompts_before = self.prompts
            self.prompts = ClassicPrompts(self)
        elif self._prompts_before:
            self.prompts = self._prompts_before
            self._prompts_before = None


InteractiveShellABC.register(TerminalInteractiveShell)

if __name__ == '__main__':
    TerminalInteractiveShell.instance().interact()
