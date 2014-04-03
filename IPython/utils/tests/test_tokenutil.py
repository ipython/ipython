"""Tests for tokenutil"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import nose.tools as nt

from IPython.utils.tokenutil import token_at_cursor

def expect_token(expected, cell, cursor_pos):
    token = token_at_cursor(cell, cursor_pos)
    offset = 0
    for line in cell.splitlines():
        if offset + len(line) >= cursor_pos:
            break
        else:
            offset += len(line)
    column = cursor_pos - offset
    line_with_cursor = '%s|%s' % (line[:column], line[column:])
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
    start = cell.index(expected)
    for i in range(start, start + len(expected)):
        expect_token(expected, cell, i)
    expected = 'there'
    start = cell.index(expected)
    for i in range(start, start + len(expected)):
        expect_token(expected, cell, i)

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
