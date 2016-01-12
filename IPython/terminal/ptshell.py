from IPython.core.interactiveshell import InteractiveShell

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import HasFocus, HasSelection
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import create_prompt_application
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.styles import PygmentsStyle

from pygments.lexers import Python3Lexer
from pygments.token import Token


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
            yield Completion(m, start_position=start_pos)


class PTInteractiveShell(InteractiveShell):
    colors_force = True

    pt_cli = None

    def get_prompt_tokens(self, cli):
        return [
            (Token.Prompt, 'In ['),
            (Token.PromptNum, str(self.execution_count)),
            (Token.Prompt, ']: '),
        ]


    def init_prompt_toolkit_cli(self):
        kbmanager = KeyBindingManager.for_prompt()
        # Ctrl+J == Enter, seemingly
        @kbmanager.registry.add_binding(Keys.ControlJ,
                            filter=HasFocus(DEFAULT_BUFFER) & ~HasSelection())
        def _(event):
            b = event.current_buffer
            if not b.document.on_last_line:
                b.newline()
                return

            status, indent = self.input_splitter.check_complete(b.document.text)

            if (status != 'incomplete') and b.accept_action.is_returnable:
                b.accept_action.validate_and_handle(event.cli, b)
            else:
                b.insert_text('\n' + (' ' * (indent or 0)))

        @kbmanager.registry.add_binding(Keys.ControlC)
        def _(event):
            event.current_buffer.reset()

        # Pre-populate history from IPython's history database
        history = InMemoryHistory()
        last_cell = u""
        for _, _, cell in self.history_manager.get_tail(self.history_load_length,
                                                        include_latest=True):
            # Ignore blank lines and consecutive duplicates
            cell = cell.rstrip()
            if cell and (cell != last_cell):
                history.append(cell)

        style = PygmentsStyle.from_defaults({
            Token.Prompt: '#009900',
            Token.PromptNum: '#00ff00 bold',
            Token.Number: '#007700',
            Token.Operator: '#bbbbbb',
        })

        app = create_prompt_application(multiline=True,
                            lexer=PygmentsLexer(Python3Lexer),
                            get_prompt_tokens=self.get_prompt_tokens,
                            key_bindings_registry=kbmanager.registry,
                            history=history,
                            completer=IPythonPTCompleter(self.Completer),
                            enable_history_search=True,
                            style=style,
        )

        self.pt_cli = CommandLineInterface(app)

    def __init__(self, *args, **kwargs):
        super(PTInteractiveShell, self).__init__(*args, **kwargs)
        self.init_prompt_toolkit_cli()
        self.keep_running = True

    def ask_exit(self):
        self.keep_running = False

    def interact(self):
        while self.keep_running:
            print(self.separate_in, end='')
            try:
                document = self.pt_cli.run()
            except EOFError:
                if self.ask_yes_no('Do you really want to exit ([y]/n)?','y','n'):
                    self.ask_exit()

            else:
                if document:
                    self.run_cell(document.text, store_history=True)


if __name__ == '__main__':
    PTInteractiveShell.instance().interact()
