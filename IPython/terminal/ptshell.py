from IPython.core.interactiveshell import InteractiveShell

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.shortcuts import create_prompt_layout
from prompt_toolkit.filters import Condition
from prompt_toolkit.interface import AcceptAction, Application, CommandLineInterface
from prompt_toolkit.layout.lexers import PygmentsLexer

from pygments.lexers import Python3Lexer
from pygments.token import Token


class PTInteractiveShell(InteractiveShell):
    def _multiline(self, cli):
        doc = cli.current_buffer.document
        if not doc.on_last_line:
            cli.run_in_terminal(lambda: print('Not on last line'))
            return False
        status, indent = self.input_splitter.check_complete(doc.text)
        return status == 'incomplete'

    def _multiline2(self):
        return self._multiline(self.pt_cli)

    pt_cli = None

    def get_prompt_tokens(self, cli):
        return [
            (Token.Prompt, 'In ['),
            (Token.Prompt, str(self.execution_count)),
            (Token.Prompt, ']: '),
        ]


    def init_prompt_toolkit_cli(self):
        layout = create_prompt_layout(
            get_prompt_tokens=self.get_prompt_tokens,
            lexer=PygmentsLexer(Python3Lexer),
            multiline=Condition(self._multiline),
        )
        buffer = Buffer(
            is_multiline=Condition(self._multiline2),
            accept_action=AcceptAction.RETURN_DOCUMENT,
        )
        app = Application(layout=layout, buffer=buffer)
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
                self.run_cell(document.text)


if __name__ == '__main__':
    PTInteractiveShell().interact()
