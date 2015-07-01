"""
"""
from __future__ import unicode_literals

from prompt_toolkit import AbortAction
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.completion import Completer, Completion
#from prompt_toolkit.history import FileHistory, History
from prompt_toolkit.interface import CommandLineInterface, Application, AcceptAction
from prompt_toolkit.key_binding.manager import KeyBindingManager

from .key_bindings import load_python_bindings
from .layout import create_layout
from .style import get_style
from .utils import document_is_multiline_python

from pygments.lexers import PythonLexer

__all__ = (
    'PythonInput',
    'PythonCommandLineInterface',
)


class PythonInput(object):
    """
    Prompt for reading Python input.

    ::

        python_input = PythonInput(...)
        application = python_input.create_application()
        cli = CommandLineInterface(application=application)
        python_code = cli.run()
    """
    def __init__(self,
                  ipython_readline_completer,
#                 history_filename=None,
                 _accept_action=AcceptAction.RETURN_DOCUMENT,
                 _on_exit=AbortAction.RAISE_EXCEPTION):

#        self._history = FileHistory(history_filename) if history_filename else History()
        self._lexer = PythonLexer
        self._accept_action = _accept_action
        self._on_exit = _on_exit

        self.ipython_readline_completer = ipython_readline_completer

        # Settings.
        self.prompt = '>> '
        self.show_completions_menu = True
        self.complete_while_typing = False
        self.vi_mode = False #vi_mode
        self.paste_mode = False  # When True, don't insert whitespace after newline.
        self.enable_history_search = False  # When True, like readline, going
                                            # back in history will filter the
                                            # history on the records starting
                                            # with the current input.

        # Use a KeyBindingManager for loading the key bindings.
        self.key_bindings_manager = KeyBindingManager(
            enable_vi_mode=Condition(lambda cli: self.vi_mode),
            enable_open_in_editor=True,
            enable_system_bindings=True)

        load_python_bindings(self.key_bindings_manager, self)

    def create_application(self):
        """
        Create an `Application` instance for use in a `CommandLineInterface`.
        """
        return Application(
            layout=create_layout(
                self,
                self.key_bindings_manager,
                lexer=self._lexer),
            buffer=self._create_buffer(),
            key_bindings_registry=self.key_bindings_manager.registry,
            paste_mode=Condition(lambda cli: self.paste_mode),
            on_abort=AbortAction.RETRY,
            on_exit=self._on_exit,
            style=get_style())

    def _create_buffer(self):
        """
        Create the `Buffer` for the Python input.
        """
        def is_buffer_multiline():
            return (self.paste_mode or
                    document_is_multiline_python(python_buffer.document))

        python_buffer = Buffer(
            is_multiline=Condition(is_buffer_multiline),
            complete_while_typing=Condition(lambda: self.complete_while_typing),
            enable_history_search=Condition(lambda: self.enable_history_search),
            tempfile_suffix='.py',
#            history=self._history,
            completer=IPythonCompleter(self.ipython_readline_completer),
            accept_action=self._accept_action)

        return python_buffer

    def on_reset(self, cli):
        self.key_bindings_manager.reset()


class PythonCommandLineInterface(CommandLineInterface):
    def __init__(self, eventloop=None, input=None, output=None):
        python_input = PythonInput()

        super(PythonCommandLineInterface, self).__init__(
            application=python_input.create_application(),
            eventloop=eventloop,
            input=input,
            output=output)


class IPythonCompleter(Completer):
    def __init__(self, ipython_readline_completer):
        self.ipython_readline_completer = ipython_readline_completer

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        if word_before_cursor:
            a, completions = self.ipython_readline_completer.complete(word_before_cursor, word_before_cursor, len(word_before_cursor))

            for c in completions:
                yield Completion(c, start_position=-len(word_before_cursor), display=c)
