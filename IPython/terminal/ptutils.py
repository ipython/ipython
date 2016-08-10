"""prompt-toolkit utilities

Everything in this module is a private API,
not to be used outside IPython.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import unicodedata
from wcwidth import wcwidth

from IPython.utils.py3compat import PY3

from IPython.core.completer import IPCompleter
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.layout.lexers import Lexer
from prompt_toolkit.layout.lexers import PygmentsLexer

import pygments.lexers as pygments_lexers


class IPythonPTCompleter(Completer):
    """Adaptor to provide IPython completions to prompt_toolkit"""
    def __init__(self, ipy_completer=None, shell=None):
        if shell is None and ipy_completer is None:
            raise TypeError("Please pass shell=an InteractiveShell instance.")
        self._ipy_completer = ipy_completer
        self.shell = shell

    @property
    def ipy_completer(self):
        if self._ipy_completer:
            return self._ipy_completer
        else:
            return self.shell.Completer

    def get_completions(self, document, complete_event):
        if not document.current_line.strip():
            return

        used, matches = self.ipy_completer.complete(
                            line_buffer=document.current_line,
                            cursor_pos=document.cursor_position_col
        )
        start_pos = -len(used)
        for m in matches:
            if not m:
                # Guard against completion machinery giving us an empty string.
                continue

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

            # TODO: Use Jedi to determine meta_text
            # (Jedi currently has a bug that results in incorrect information.)
            # meta_text = ''
            # yield Completion(m, start_position=start_pos,
            #                  display_meta=meta_text)
            yield Completion(m, start_position=start_pos)

class IPythonPTLexer(Lexer):
    """
    Wrapper around PythonLexer and BashLexer.
    """
    def __init__(self):
        l = pygments_lexers
        self.python_lexer = PygmentsLexer(l.Python3Lexer if PY3 else l.PythonLexer)
        self.shell_lexer = PygmentsLexer(l.BashLexer)

        self.magic_lexers = {
            'HTML': PygmentsLexer(l.HtmlLexer),
            'html': PygmentsLexer(l.HtmlLexer),
            'javascript': PygmentsLexer(l.JavascriptLexer),
            'js': PygmentsLexer(l.JavascriptLexer),
            'perl': PygmentsLexer(l.PerlLexer),
            'ruby': PygmentsLexer(l.RubyLexer),
            'latex': PygmentsLexer(l.TexLexer),
        }

    def lex_document(self, cli, document):
        text = document.text.lstrip()

        lexer = self.python_lexer

        if text.startswith('!') or text.startswith('%%bash'):
            lexer = self.shell_lexer

        elif text.startswith('%%'):
            for magic, l in self.magic_lexers.items():
                if text.startswith('%%' + magic):
                    lexer = l
                    break

        return lexer.lex_document(cli, document)
