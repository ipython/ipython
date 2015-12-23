from IPython.core.interactiveshell import InteractiveShell

from prompt_toolkit.shortcuts import create_prompt_application
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.lexers import PygmentsLexer

from pygments.lexers import Python3Lexer
from pygments.token import Token


class PTInteractiveShell(InteractiveShell):
    pt_cli = None

    def get_prompt_tokens(self, cli):
        return [
            (Token.Prompt, 'In ['),
            (Token.Prompt, str(self.execution_count)),
            (Token.Prompt, ']: '),
        ]


    def init_prompt_toolkit_cli(self):
        kbmanager = KeyBindingManager.for_prompt()
        @kbmanager.registry.add_binding(Keys.ControlJ) # Ctrl+J == Enter, seemingly
        def _(event):
            b = event.current_buffer
            if not b.document.on_last_line:
                b.newline()
                return

            status, indent = self.input_splitter.check_complete(b.document.text)

            if (status != 'incomplete') and b.accept_action.is_returnable:
                b.accept_action.validate_and_handle(event.cli, b)
            else:
                b.insert_text('\n' + (' ' * indent))

        app = create_prompt_application(multiline=True,
                            lexer=PygmentsLexer(Python3Lexer),
                            get_prompt_tokens=self.get_prompt_tokens,
                            key_bindings_registry=kbmanager.registry,
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
            document = self.pt_cli.run()
            if document:
                self.run_cell(document.text, store_history=True)


if __name__ == '__main__':
    PTInteractiveShell().interact()
