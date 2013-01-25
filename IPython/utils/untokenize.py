"""This is a patched copy of the untokenize machinery from the standard library.

untokenize has a number of major bugs that render it almost useless. We're using
the patch written by Gareth Rees on Python issue 12961:

http://bugs.python.org/issue12691

We've undone one part of the patch - it encoded the output to bytes, to neatly
round-trip from tokenize. We want to keep working with text, so we don't encode.
"""

__author__ = 'Ka-Ping Yee <ping@lfw.org>'
__credits__ = ('GvR, ESR, Tim Peters, Thomas Wouters, Fred Drake, '
               'Skip Montanaro, Raymond Hettinger, Trent Nelson, '
               'Michael Foord')
from token import *


from tokenize import COMMENT, NL

try:
    # Python 3
    from tokenize import ENCODING
except:
    ENCODING = 987654321

class Untokenizer:

    def __init__(self):
        self.tokens = []
        self.prev_row = 1
        self.prev_col = 0
        self.encoding = 'utf-8'

    def add_whitespace(self, tok_type, start):
        row, col = start
        assert row >= self.prev_row
        col_offset = col - self.prev_col
        if col_offset > 0:
            self.tokens.append(" " * col_offset)
        elif row > self.prev_row and tok_type not in (NEWLINE, NL, ENDMARKER):
            # Line was backslash-continued.
            self.tokens.append(" ")

    def untokenize(self, tokens):
        iterable = iter(tokens)
        for t in iterable:
            if len(t) == 2:
                self.compat(t, iterable)
                break
            # IPython modification - valid Python 2 syntax
            tok_type, token, start, end = t[:4]
            if tok_type == ENCODING:
                self.encoding = token
                continue
            self.add_whitespace(tok_type, start)
            self.tokens.append(token)
            self.prev_row, self.prev_col = end
            if tok_type in (NEWLINE, NL):
                self.prev_row += 1
                self.prev_col = 0
        # IPython modification - don't encode output
        return "".join(self.tokens)

    def compat(self, token, iterable):
        # This import is here to avoid problems when the itertools
        # module is not built yet and tokenize is imported.
        from itertools import chain
        startline = False
        prevstring = False
        indents = []
        toks_append = self.tokens.append

        for tok in chain([token], iterable):
            toknum, tokval = tok[:2]
            if toknum == ENCODING:
                self.encoding = tokval
                continue

            if toknum in (NAME, NUMBER):
                tokval += ' '

            # Insert a space between two consecutive strings
            if toknum == STRING:
                if prevstring:
                    tokval = ' ' + tokval
                prevstring = True
            else:
                prevstring = False

            if toknum == INDENT:
                indents.append(tokval)
                continue
            elif toknum == DEDENT:
                indents.pop()
                continue
            elif toknum in (NEWLINE, NL):
                startline = True
            elif startline and indents:
                toks_append(indents[-1])
                startline = False
            toks_append(tokval)


def untokenize(tokens):
    """
    Convert ``tokens`` (an iterable) back into Python source code. Return
    a bytes object, encoded using the encoding specified by the last
    ENCODING token in ``tokens``, or UTF-8 if no ENCODING token is found.

    The result is guaranteed to tokenize back to match the input so that
    the conversion is lossless and round-trips are assured.  The
    guarantee applies only to the token type and token string as the
    spacing between tokens (column positions) may change.

    :func:`untokenize` has two modes. If the input tokens are sequences
    of length 2 (``type``, ``string``) then spaces are added as necessary to
    preserve the round-trip property.

    If the input tokens are sequences of length 4 or more (``type``,
    ``string``, ``start``, ``end``), as returned by :func:`tokenize`, then
    spaces are added so that each token appears in the result at the
    position indicated by ``start`` and ``end``, if possible.
    """
    return Untokenizer().untokenize(tokens)
