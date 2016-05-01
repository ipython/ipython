"""IPython terminal interface using prompt_toolkit in place of readline"""
from __future__ import print_function

import os
import sys
import signal
import unicodedata
from warnings import warn
from wcwidth import wcwidth

from IPython.core.error import TryNext
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.py3compat import PY3, cast_unicode_py2, input
from IPython.utils.terminal import toggle_set_term_title, set_term_title
from IPython.utils.process import abbrev_cwd
from traitlets import Bool, CBool, Unicode, Dict, Integer

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER
from prompt_toolkit.filters import HasFocus, HasSelection, Condition
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import create_prompt_application, create_eventloop, create_prompt_layout
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.key_binding.bindings.vi import ViStateFilter
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.lexers import Lexer
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.styles import PygmentsStyle, DynamicStyle

from pygments.styles import get_style_by_name, get_all_styles
from pygments.lexers import Python3Lexer, BashLexer, PythonLexer
from pygments.token import Token

from .pt_inputhooks import get_inputhook_func
from .interactiveshell import get_default_editor, TerminalMagics


class IPythonPTCompleter(Completer):
    """Adaptor to provide IPython completions to prompt_toolkit"""
    def __init__(self, ipy_completer):
        self.ipy_completer = ipy_completer

    def get_completions(self, document, complete_event):
        if not document.current_line.strip():
            return

        used, matches = self.ipy_completer.complete(
                            line_buffer=document.current_line,
                            cursor_pos=document.cursor_position_col
        )
        start_pos = -len(used)
        for m in matches:
            m = unicodedata.normalize('NFC', m)

            # When the first character of the completion has a zero length,
            # then it's probably a decomposed unicode character. E.g. caused by
            # the "\dot" completion. Try to compose again with the previous
            # character.
            if wcwidth(m[0]) == 0:
                if document.cursor_position + start_pos > 0:
                    char_before = document.text[document.cursor_position + start_pos - 1]
                    m = unicodedata.normalize('NFC', char_before + m)

                    # Yield the modified completion instead, if this worked.
                    if wcwidth(m[0:1]) == 1:
                        yield Completion(m, start_position=start_pos - 1)
                        continue

            yield Completion(m, start_position=start_pos)


class IPythonPTLexer(Lexer):
    """
    Wrapper around PythonLexer and BashLexer.
    """
    def __init__(self):
        self.python_lexer = PygmentsLexer(Python3Lexer if PY3 else PythonLexer)
        self.shell_lexer = PygmentsLexer(BashLexer)

    def lex_document(self, cli, document):
        if document.text.startswith('!'):
            return self.shell_lexer.lex_document(cli, document)
        else:
            return self.python_lexer.lex_document(cli, document)


class TerminalInteractiveShell(InteractiveShell):
    colors_force = True

    space_for_menu = Integer(6, config=True, help='Number of line at the bottom of the screen '
                                                  'to reserve for the completion menu')

    def _space_for_menu_changed(self, old, new):
        self._update_layout()

    pt_cli = None

    autoedit_syntax = CBool(False, config=True,
                            help="auto editing of files with syntax errors.")

    confirm_exit = CBool(True, config=True,
        help="""
        Set to confirm when you try to exit IPython with an EOF (Control-D
        in Unix, Control-Z/Enter in Windows). By typing 'exit' or 'quit',
        you can force a direct exit without any confirmation.""",
    )
    vi_mode = Bool(False, config=True,
        help="Use vi style keybindings at the prompt",
    )

    mouse_support = Bool(False, config=True,
        help="Enable mouse support in the prompt"
    )

    highlighting_style = Unicode('default', config=True,
            help="The name of a Pygments style to use for syntax highlighting: \n %s" % ', '.join(get_all_styles())
    )

    def _highlighting_style_changed(self, old, new):
        self._style = self._make_style_from_name(self.highlighting_style)

    highlighting_style_overrides = Dict(config=True,
        help="Override highlighting format for specific tokens"
    )

    editor = Unicode(get_default_editor(), config=True,
        help="Set the editor used by IPython (default to $EDITOR/vi/notepad)."
    )
    
    term_title = Bool(True, config=True,
        help="Automatically set the terminal title"
    )
    def _term_title_changed(self, name, new_value):
        self.init_term_title()
    
    def init_term_title(self):
        # Enable or disable the terminal title.
        if self.term_title:
            toggle_set_term_title(True)
            set_term_title('IPython: ' + abbrev_cwd())
        else:
            toggle_set_term_title(False)

    def get_prompt_tokens(self, cli):
        return [
            (Token.Prompt, 'In ['),
            (Token.PromptNum, str(self.execution_count)),
            (Token.Prompt, ']: '),
        ]

    def get_continuation_tokens(self, cli, width):
        return [
            (Token.Prompt, (' ' * (width - 5)) + '...: '),
        ]

    def init_prompt_toolkit_cli(self):
        if ('IPY_TEST_SIMPLE_PROMPT' in os.environ) or not sys.stdin.isatty():
            # Fall back to plain non-interactive output for tests.
            # This is very limited, and only accepts a single line.
            def prompt():
                return cast_unicode_py2(input('In [%d]: ' % self.execution_count))
            self.prompt_for_code = prompt
            return

        kbmanager = KeyBindingManager.for_prompt(enable_vi_mode=self.vi_mode)
        insert_mode = ViStateFilter(kbmanager.get_vi_state, InputMode.INSERT)
        # Ctrl+J == Enter, seemingly
        @kbmanager.registry.add_binding(Keys.ControlJ,
                            filter=(HasFocus(DEFAULT_BUFFER)
                                    & ~HasSelection()
                                    & insert_mode
                                   ))
        def _(event):
            b = event.current_buffer
            d = b.document
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
        def _(event):
            event.current_buffer.reset()

        @kbmanager.registry.add_binding(Keys.ControlC, filter=HasFocus(SEARCH_BUFFER))
        def _(event):
            if event.current_buffer.document.text:
                event.current_buffer.reset()
            else:
                event.cli.push_focus(DEFAULT_BUFFER)

        supports_suspend = Condition(lambda cli: hasattr(signal, 'SIGTSTP'))

        @kbmanager.registry.add_binding(Keys.ControlZ, filter=supports_suspend)
        def _(event):
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
        def _(event):
            event.current_buffer.insert_text(' ' * 4)

        # Pre-populate history from IPython's history database
        history = InMemoryHistory()
        last_cell = u""
        for _, _, cell in self.history_manager.get_tail(self.history_load_length,
                                                        include_latest=True):
            # Ignore blank lines and consecutive duplicates
            cell = cell.rstrip()
            if cell and (cell != last_cell):
                history.append(cell)

        self._style = self._make_style_from_name(self.highlighting_style)
        style = DynamicStyle(lambda: self._style)

        self._app = create_prompt_application(
                            key_bindings_registry=kbmanager.registry,
                            history=history,
                            completer=IPythonPTCompleter(self.Completer),
                            enable_history_search=True,
                            style=style,
                            mouse_support=self.mouse_support,
                            **self._layout_options()
        )
        self.pt_cli = CommandLineInterface(self._app,
                           eventloop=create_eventloop(self.inputhook))

    def _make_style_from_name(self, name):
        """
        Small wrapper that make an IPython compatible style from a style name

        We need that to add style for prompt ... etc. 
        """
        style_cls = get_style_by_name(name)
        style_overrides = {
            Token.Prompt: '#009900',
            Token.PromptNum: '#00ff00 bold',
        }
        if name is 'default':
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
                'get_prompt_tokens':self.get_prompt_tokens,
                'get_continuation_tokens':self.get_continuation_tokens,
                'multiline':True,
                }


    def _update_layout(self):
        """
        Ask for a re computation of the application layout, if for example ,
        some configuration options have changed.
        """
        self._app.layout = create_prompt_layout(**self._layout_options())

    def prompt_for_code(self):
        document = self.pt_cli.run(pre_run=self.pre_prompt)
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


if __name__ == '__main__':
    TerminalInteractiveShell.instance().interact()
