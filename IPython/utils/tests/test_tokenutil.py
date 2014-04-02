"""Tests for tokenutil"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import nose.tools as nt

from IPython.utils.tokenutil import token_at_cursor

def expect_token(expected, cell, column, line=0):
    token = token_at_cursor(cell, column, line)
    
    lines = cell.splitlines()
    line_with_cursor = '%s|%s' % (lines[line][:column], lines[line][column:])
    line
    nt.assert_equal(token, expected,
        "Excpected %r, got %r in: %s" % (
        expected, token, line_with_cursor)
    )

def test_simple(): 
    cell = "foo"
    for i in range(len(cell)):
        expect_token("foo", cell, i)

def test_function():
    cell = "foo(a=5, b='10')"
    expected = 'foo'
    for i in (6,7,8,10,11,12):
        expect_token("foo", cell, i)

def test_multiline():
    cell = '\n'.join([
        'a = 5',
        'b = hello("string", there)'
    ])
    expected = 'hello'
    for i in range(4,9):
        expect_token(expected, cell, i, 1)
    expected = 'there'
    for i in range(21,27):
        expect_token(expected, cell, i, 1)

def test_attrs():
    cell = "foo(a=obj.attr.subattr)"
    expected = 'obj'
    idx = cell.find('obj')
    for i in range(idx, idx + 3):
        expect_token(expected, cell, i)
    idx = idx + 4
    expected = 'obj.attr'
    for i in range(idx, idx + 4):
        expect_token(expected, cell, i)
    idx = idx + 5
    expected = 'obj.attr.subattr'
    for i in range(idx, len(cell)):
        expect_token(expected, cell, i)
