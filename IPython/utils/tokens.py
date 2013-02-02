# encoding: utf-8
"""
Utilities for tokenizing source code and processesing those tolens
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import StringIO
import inspect
import tokenize as _tokenizelib
import re

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def tokenize(src):
    """Tokenize a block of python source code using the stdlib's tokenizer.

    Parameters
    ----------
    src : str
        A string of potential python source code. The code isn't evaled, it's
        just split into its representive tokens

    Returns
    -------
    tokens : list of strings
        A list of tokens. Tokenizer errors from invalid python source (like
        unclosed string delimiters) are supressed.

    Examples
    --------
    In [1]: tokenize('a + b = ["cdefg" + 10]')
    ['a', '+', 'b', '=', '[', '"cdefg"', '+', '10', ']']

    Notes
    -----
    This serves a similar function to simply splitting the source on delmiters
    (as done by CompletionSplitter) but is slightly more sophisticated. In
    particular, characters that are delmiters are never returned in the tokens
    by CompletionSplitter (or its regular expression engine), so something
    like this happens:

    In[2]: a = CompletionSplitter()._delim_re.split('a+ "hello')
    In[3]: b = CompletionSplitter()._delim_re.split('a+= hello')
    In[4]: a == b
    True

    This makes it very tricky to do complicated types of tab completion.

    This tokenizer instead uses the stdlib's tokenize, which is a little
    bit more knowledgeable about python syntax. In particular, string literals
    e.g. `tokenize("'a' + '''bc'''") == ["'a'", "+", "'''bc'''"]` get parsed
    as single tokens.
    """
    rawstr = StringIO.StringIO(src)
    iter_tokens = _tokenizelib.generate_tokens(rawstr.readline)
    def run():
        try:
            for toktype, toktext, (srow,scol), (erow,ecol), line  in iter_tokens:
                if toktype != _tokenizelib.ENDMARKER:
                    yield toktext
        except _tokenizelib.TokenError:
            pass
    tokens = list(run())
    return tokens


def last_open_identifier(tokens):
    """Find the the nearest identifier (function/method/callable name)
    that comes before the last unclosed parentheses

    Parameters
    ----------
    tokens : list of strings
        tokens should be a list of python tokens produced by splitting
        a line of input

    Returns
    -------
    identifiers : list
        A list of tokens from `tokens` that are identifiers for the function
        or method that comes before an unclosed partentheses
    call_tokens : list
        The subset of the tokens that occur after `identifiers` in the input,
        starting with the open parentheses of the function call

    Raises
    ------
    ValueError if the line doesn't match

    See Also
    --------
    tokenize : to generate `tokens`
    cursor_argument
    """

    # 1. pop off the tokens until we get to the first unclosed parens
    # as we pop them off, store them in a list
    iterTokens = iter(reversed(tokens))
    tokens_after_identifier = []

    openPar = 0 # number of open parentheses
    for token in iterTokens:
        tokens_after_identifier.insert(0, token)
        if token == ')':
            openPar -= 1
        elif token == '(':
            openPar += 1
            if openPar > 0:
                # found the last unclosed parenthesis
                break
    else:
        raise ValueError()

    # 2. Concatenate dotted names ("foo.bar" for "foo.bar(x, pa" )
    identifiers = []
    isId = re.compile(r'\w+$').match
    while True:
        try:
            identifiers.append(next(iterTokens))
            if not isId(identifiers[-1]):
                identifiers.pop(); break
            if not next(iterTokens) == '.':
                break
        except StopIteration:
            break

    return identifiers[::-1], tokens_after_identifier


def last_function_chain(tokens):
    """Find the last open chain of function/method/callables in a set of tokens.
    
    Examples
    --------
    In [8]: src = "var = foo(bar().qux().baz"

    In [9]: last_function_chain(tokenize(src))
    Out[9]: ['bar', '(', ')', '.', 'qux', '(', ')', '.', 'baz']
    """
    last_chain = []
    n_open_parens = 0
    for token in iter(reversed(tokens)):
        if token == '(':
            n_open_parens += 1
        elif token == ')':
            n_open_parens -= 1
        if n_open_parens > 0:
            break
        if token in set(['=', ':', '{']) and n_open_parens == 0:
            break
        last_chain.insert(0, token)
        
    return last_chain


class MatchingDelimiterCounter(object):
    """Little utility class for counting the current
    number of various types of matching delimiters in
    tokenized input.
    
    Attributes
    ----------
    n_open_parens : int
        Current number of open parentheses
    n_open_braces : int
        Current number of open curly braces 
    n_open_bracket : int
        Current number of open square brackets
    """

    def __init__(self):
        self.n_open_parens = 0
        self.n_open_braces = 0
        self.n_open_brackets = 0
        self._dispatch = {
            '(': self._open_paren,
            ')': self._close_paren,
            '{': self._open_brace,
            '}': self._close_brace,
            '[': self._open_bracket,
            ']': self._close_bracket
        }
    
    def push(self, token):
        """Push a new token onto the counter
        
        Returns
        -------
        matched : bool
            True if the token was matched, false otherwise.
        """
        if token in self._dispatch:
            self._dispatch[token]()
            return True
        return False
    
    def _open_paren(self):
        self.n_open_parens += 1
    def _close_paren(self):
        self.n_open_parens -= 1
    def _open_bracket(self):
        self.n_open_brackets += 1
    def _close_bracket(self):
        self.n_open_brackets -= 1
    def _open_brace(self):
        self.n_open_braces += 1
    def _close_brace(self):
        self.n_open_braces -= 1


def cursor_argument(call_tokens, obj):
    """Determine which argument the cursor is currently entering

    Parameters
    ----------
    call_tokens : str
        Tokens after the last unclosed parentheses on the current
        line, starting with an open parens
    obj : callable
        The function or method being called

    Returns
    -------
    argname : str, None
        the name of one of the arguments to the function, or None

    Examples
    --------
    In[5]: def foo(x, y, z):
    ...        pass
    In[6]: call_tokens == ['(', '1', ',', 'bar']
    True
    In[7]: cursor_argument(call_tokens, foo)
    'y'

    See ALso
    --------
    tokenize
    """
    try:
        argspec = inspect.getargspec(obj)
    except ValueError:
        # python3
        argspec = inspect.getfullargspec(obj)
    
    if call_tokens[0] != '(':
        raise ValueError('The first token must be "(". You supplied %s' \
            % call_tokens[0])
    n_commas = 0
    counter = MatchingDelimiterCounter()
    prev_token = None
    
    for token in call_tokens[1:]:  # ignore first open parens
        if (counter.n_open_parens == 0) and (counter.n_open_braces == 0) and \
                (counter.n_open_brackets == 0):
            if token == '=':
                # short circuit this stuff, they're using a named argument, so we'll
                # just take that name
                return prev_token
            if token == ',':
                n_commas += 1

        counter.push(token)
        prev_token = token
        
    if inspect.ismethod(obj):
        # need to ignore self
        return argspec.args[n_commas+1]

    return argspec.args[n_commas]
