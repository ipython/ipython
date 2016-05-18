from pygments.token import Token

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
        in_tokens = self.in_prompt_tokens()
        return sum(len(s) for (t, s) in in_tokens)

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
