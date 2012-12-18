# encoding: utf-8
"""Tests for IPython.utils.tokens"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from IPython.utils import tokens

# third party
import nose.tools as nt

#-----------------------------------------------------------------------------
# Test tokenize
#-----------------------------------------------------------------------------

def test_tokenize_1():
    got = tokens.tokenize('a + b = ["cdefg" + 10]')
    correct = ['a', '+', 'b', '=', '[', '"cdefg"', '+', '10', ']']
    
    nt.assert_equal(got, correct)
    
def test_tokenize_2():
    # make sure the contents of string literals ges parsed as a single tokens
    # including inside of tripple quotes.
    got = tokens.tokenize("'a/b' + '''b\nc'''")
    correct = ["'a/b'", "+", "'''b\nc'''"]
    
    nt.assert_equal(got, correct)


#-----------------------------------------------------------------------------
# Test last_open_identifier
#-----------------------------------------------------------------------------

def test_last_open_identifier_1():
    src = "f(a, b, c"
    identifier, call_tokens = tokens.last_open_identifier(tokens.tokenize(src))
    correct_identifier = ['f']
    correct_call_tokens = ['(', 'a', ',', 'b', ',', 'c']
    
    nt.assert_equal(identifier, correct_identifier)
    nt.assert_equal(call_tokens, correct_call_tokens)
    
def test_last_open_identifier_2():
    src = "foo.bar(a, b, c"
    identifier, call_tokens = tokens.last_open_identifier(tokens.tokenize(src))
    correct_identifier = ['foo', 'bar']
    correct_call_tokens = ['(', 'a', ',', 'b', ',', 'c']
    
    nt.assert_equal(identifier, correct_identifier)
    nt.assert_equal(call_tokens, correct_call_tokens)
    
def test_last_open_identifier_3():
    src = 'foo((a,b), c'
    identifier, call_tokens = tokens.last_open_identifier(tokens.tokenize(src))
    correct_identifier = ['foo']
    correct_call_tokens = ['(', '(', 'a', ',', 'b', ')', ',', 'c']
    
    nt.assert_equal(identifier, correct_identifier)
    nt.assert_equal(call_tokens, correct_call_tokens)

def test_last_open_identifier_4():
    src = 'foo("a,b", c'
    identifier, call_tokens = tokens.last_open_identifier(tokens.tokenize(src))
    correct_identifier = ['foo']
    correct_call_tokens = ['(', '"a,b"', ',', 'c']
    
    nt.assert_equal(identifier, correct_identifier)
    nt.assert_equal(call_tokens, correct_call_tokens)

#-----------------------------------------------------------------------------
# Test last_function_chain
#-----------------------------------------------------------------------------

def test_last_function_chain_1():
    src = "var = foobar(bar().qux().baz"
    got = tokens.last_function_chain(tokens.tokenize(src))
    correct = ['bar', '(', ')', '.', 'qux', '(', ')', '.', 'baz']
    nt.assert_equal(got, correct)

def test_last_function_chain_2():
    src = 'var = bar("(abc").qux.baz'
    got = tokens.last_function_chain(tokens.tokenize(src))
    correct = ['bar', '(', '"(abc"', ')', '.', 'qux', '.', 'baz']
    nt.assert_equal(got, correct)

def test_last_function_chain_3():
    src = 'bar().qux.baz'
    got = tokens.last_function_chain(tokens.tokenize(src))
    correct = ['bar', '(', ')', '.', 'qux', '.', 'baz']
    nt.assert_equal(got, correct)

def test_last_function_chain_4():
    src = '{"a": bar().qux.baz'
    got = tokens.last_function_chain(tokens.tokenize(src))
    correct = ['bar', '(', ')', '.', 'qux', '.', 'baz']
    nt.assert_equal(got, correct)

def test_last_function_chain_5():
    src = '{bar().qux.baz'
    got = tokens.last_function_chain(tokens.tokenize(src))
    correct = ['bar', '(', ')', '.', 'qux', '.', 'baz']
    nt.assert_equal(got, correct)

def test_last_function_chain_6():
    src = '(bar().qux.baz'
    got = tokens.last_function_chain(tokens.tokenize(src))
    correct = ['bar', '(', ')', '.', 'qux', '.', 'baz']
    nt.assert_equal(got, correct)

#-----------------------------------------------------------------------------
# Test cursor_argument
#-----------------------------------------------------------------------------

def test_cursor_argument_1():
    def f(aa, bb=1, cc=1):
        pass
    call_src = "(a, b, c"
    call_tokens = tokens.tokenize(call_src)
    nt.assert_equal('cc', tokens.cursor_argument(call_tokens, f))

def test_cursor_argument_2():
    def f(aa, bb=1, cc=1):
        pass
    call_src = "(a, cc="
    call_tokens = tokens.tokenize(call_src)
    nt.assert_equal('cc', tokens.cursor_argument(call_tokens, f))

def test_cursor_argument_3():
    def f(aa, bb=1, cc=1):
        pass
    call_src = "(a, {a:b, c"
    call_tokens = tokens.tokenize(call_src)
    nt.assert_equal('bb', tokens.cursor_argument(call_tokens, f))

def test_cursor_argument_4():
    def f(aa, bb=1, cc=1):
        pass
    call_src = "(a, (a, b"
    call_tokens = tokens.tokenize(call_src)
    nt.assert_equal('bb', tokens.cursor_argument(call_tokens, f))

def test_cursor_argument_5():
    def f(aa, bb=1, cc=1):
        pass
    call_src = "(a, (a, b), c"
    call_tokens = tokens.tokenize(call_src)
    nt.assert_equal('cc', tokens.cursor_argument(call_tokens, f))