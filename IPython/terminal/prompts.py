"""Terminal input and output prompts."""
from __future__ import print_function

from pygments.token import Token
import sys

from IPython.core.displayhook import DisplayHook

from prompt_toolkit.layout.utils import token_list_width

class Prompts(object):
    def __init__(self, shell):
        self.shell = shell

    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Prompt, 'In ['),
            (Token.PromptNum, str(self.shell.execution_count)),
            (Token.Prompt, ']: '),
        ]

    def _width(self):
        return token_list_width(self.in_prompt_tokens())

    def continuation_prompt_tokens(self, cli=None, width=None):
        if width is None:
            width = self._width()
        return [
            (Token.Prompt, (' ' * (width - 5)) + '...: '),
        ]

    def rewrite_prompt_tokens(self):
        width = self._width()
        return [
            (Token.Prompt, ('-' * (width - 2)) + '> '),
        ]

    def out_prompt_tokens(self):
        return [
            (Token.OutPrompt, 'Out['),
            (Token.OutPromptNum, str(self.shell.execution_count)),
            (Token.OutPrompt, ']: '),
        ]

class ClassicPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Prompt, '>>> '),
        ]

    def continuation_prompt_tokens(self, cli=None, width=None):
        return [
            (Token.Prompt, '... ')
        ]

    def rewrite_prompt_tokens(self):
        return []

    def out_prompt_tokens(self):
        return []

class RichPromptDisplayHook(DisplayHook):
    """Subclass of base display hook using coloured prompt"""
    def write_output_prompt(self):
        sys.stdout.write(self.shell.separate_out)
        self.prompt_end_newline = False
        if self.do_full_cache:
            tokens = self.shell.prompts.out_prompt_tokens()
            if tokens and tokens[-1][1].endswith('\n'):
                self.prompt_end_newline = True
            if self.shell.pt_cli:
                self.shell.pt_cli.print_tokens(tokens)
            else:
                print(*(s for t, s in tokens), sep='')
