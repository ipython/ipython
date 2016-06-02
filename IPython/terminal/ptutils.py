import unicodedata
from wcwidth import wcwidth

from IPython.utils.py3compat import PY3

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.layout.lexers import Lexer
from prompt_toolkit.layout.lexers import PygmentsLexer

from pygments.lexers import Python3Lexer, BashLexer, PythonLexer

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
        self.python_lexer = PygmentsLexer(Python3Lexer if PY3 else PythonLexer)
        self.shell_lexer = PygmentsLexer(BashLexer)

    def lex_document(self, cli, document):
        if document.text.startswith('!'):
            return self.shell_lexer.lex_document(cli, document)
        else:
            return self.python_lexer.lex_document(cli, document)
