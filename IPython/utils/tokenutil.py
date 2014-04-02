"""Token-related utilities"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import, print_function

from collections import namedtuple
from io import StringIO
from keyword import iskeyword

from . import tokenize2
from .py3compat import cast_unicode_py2

Token = namedtuple('Token', ['token', 'text', 'start', 'end', 'line'])

def generate_tokens(readline):
    """wrap generate_tokens to catch EOF errors"""
    try:
        for token in tokenize2.generate_tokens(readline):
            yield token
    except tokenize2.TokenError:
        # catch EOF error
        return

def token_at_cursor(cell, column, line=0):
    """Get the token at a given cursor
    
    Used for introspection.
    
    Parameters
    ----------
    
    cell : unicode
        A block of Python code
    column : int
        The column of the cursor offset, where the token should be found
    line : int, optional
        The line where the token should be found (optional if cell is a single line)
    """
    cell = cast_unicode_py2(cell)
    names = []
    tokens = []
    current_line = 0
    for tup in generate_tokens(StringIO(cell).readline):
        
        tok = Token(*tup)
        
        # token, text, start, end, line = tup
        start_col = tok.start[1]
        end_col = tok.end[1]
        if line == current_line and start_col > column:
            # current token starts after the cursor,
            # don't consume it
            break
        
        if tok.token == tokenize2.NAME and not iskeyword(tok.text):
            if names and tokens and tokens[-1].token == tokenize2.OP and tokens[-1].text == '.':
                names[-1] = "%s.%s" % (names[-1], tok.text)
            else:
                names.append(tok.text)
        elif tok.token == tokenize2.OP:
            if tok.text == '=' and names:
                # don't inspect the lhs of an assignment
                names.pop(-1)
        
        if line == current_line and end_col > column:
            # we found the cursor, stop reading
            break
        
        tokens.append(tok)
        if tok.token == tokenize2.NEWLINE:
            current_line += 1
    
    if names:
        return names[-1]
    else:
        return ''
    

