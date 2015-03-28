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

def line_at_cursor(cell, cursor_pos=0):
    """Return the line in a cell at a given cursor position
    
    Used for calling line-based APIs that don't support multi-line input, yet.
    
    Parameters
    ----------
    
    cell: text
        multiline block of text
    cursor_pos: integer
        the cursor position
    
    Returns
    -------
    
    (line, offset): (text, integer)
        The line with the current cursor, and the character offset of the start of the line.
    """
    offset = 0
    lines = cell.splitlines(True)
    for line in lines:
        next_offset = offset + len(line)
        if next_offset >= cursor_pos:
            break
        offset = next_offset
    else:
        line = ""
    return (line, offset)

def token_at_cursor(cell, cursor_pos=0):
    """Get the token at a given cursor
    
    Used for introspection.
    
    Function calls are prioritized, so the token for the callable will be returned
    if the cursor is anywhere inside the call.
    
    Parameters
    ----------
    
    cell : unicode
        A block of Python code
    cursor_pos : int
        The location of the cursor in the block where the token should be found
    """
    cell = cast_unicode_py2(cell)
    names = []
    tokens = []
    offset = 0
    call_names = []
    for tup in generate_tokens(StringIO(cell).readline):
        
        tok = Token(*tup)
        
        # token, text, start, end, line = tup
        start_col = tok.start[1]
        end_col = tok.end[1]
        # allow '|foo' to find 'foo' at the beginning of a line
        boundary = cursor_pos + 1 if start_col == 0 else cursor_pos
        if offset + start_col >= boundary:
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
            if tok.text == '(' and names:
                # if we are inside a function call, inspect the function
                call_names.append(names[-1])
            elif tok.text == ')' and call_names:
                call_names.pop(-1)
        
        if offset + end_col > cursor_pos:
            # we found the cursor, stop reading
            break
        
        tokens.append(tok)
        if tok.token == tokenize2.NEWLINE:
            offset += len(tok.line)
    
    if call_names:
        return call_names[-1]
    elif names:
        return names[-1]
    else:
        return ''
    

