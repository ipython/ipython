"""Tests for tokenutil"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import pytest
import textwrap

from IPython.utils.tokenutil import token_at_cursor, line_at_cursor


def expect_token(expected: str, cell: str, cursor_pos: int | None = None) -> None:
    """
    If cursor_pos is `None`, look for `|` as the cursor position.
    Assert that the token at the cursor position is `expected`.
    """
    if cursor_pos is None:
        assert (
            cursor_count := cell.count("|")
        ) == 1, (
            f"Cursor position not specified and found {cursor_count} instance(s) of '|'"
        )
        cursor_pos = cell.index("|")
        cell = cell.replace("|", "")
    token = token_at_cursor(cell, cursor_pos)
    offset = 0
    for line in cell.splitlines():
        if offset + len(line) >= cursor_pos:
            break
        else:
            offset += len(line) + 1
    column = cursor_pos - offset
    line_with_cursor = "%s|%s" % (line[:column], line[column:])
    assert token == expected, "Expected %r, got %r in: %r (pos %i)" % (
        expected,
        token,
        line_with_cursor,
        cursor_pos,
    )


def test_simple():
    cell = "foo"
    for i in range(len(cell)):
        expect_token("foo", cell, i)


def test_function():
    cell = "foo(a=5, b='10')"
    for i in range(len(cell)):
        expect_token("foo", cell, i)
    expect_token("a", "foo(|a, b)")
    expect_token("foo", "foo(a|, b)")
    expect_token("foo", "foo(a,| b)")
    expect_token("b", "foo(a, |b)")
    expect_token("foo", "foo(a, b|)")


@pytest.mark.parametrize(
    "cell",
    [
        "\n".join(["a = 5", "b = hello('string', there)"]),
        textwrap.dedent(
            '''
            """\n\nxxxxxxxxxx\n\n"""
            5, """
            """\n\nxxxxxxxxxx\n\n"""
            docstring
            multiline token
            """, [
            2, 3, "complicated"]
            b = hello("string", there)
        '''
        ),
    ],
)
def test_multiline(cell):
    expected = "hello"
    start = cell.index(expected) + 1
    for i in range(start, start + len(expected)):
        expect_token(expected, cell, i)
    start = cell.index(expected) + 1
    for i in range(start, start + len(expected)):
        expect_token(expected, cell, i)


def test_nested_call_kwargs():
    cell = "foo(bar(a=5), b=10)"
    start = cell.index("bar")
    last = start + len("bar")
    for i in range(start, last + 1):
        expect_token("bar", cell, i)
    start = cell.index("a=")
    for i in range(start, start + 3):
        expect_token("bar", cell, i)
    expect_token("bar", "foo(bar(a=|5), b=10)")
    expect_token("bar", "foo(bar(a=5|), b=10)")
    for i in range(cell.index(")") + 1, cell.index("b=") + 2):
        expect_token("foo", cell, i)
    expect_token("foo", cell, len(cell) - 1)


def test_nested_call_args():
    expect_token("bar", "foo(bar(x,| ))")
    expect_token("bar", "foo(bar(x, |))")
    expect_token("bar", "foo(ba|r(x, y))")
    expect_token("x", "foo(bar(|x, y))")
    expect_token("bar", "foo(bar(x|, y))")
    expect_token("bar", "foo(bar(x,| y))")
    expect_token("y", "foo(bar(x, |y))")
    expect_token("bar", "foo(bar(x, y|))")
    expect_token("foo", "foo(bar(x, y)|)")
    expect_token("foo", "foo(bar(, y)|)")


def test_outer_name():
    expect_token("x", "|x + foo(a, b) + y + z")
    expect_token("x", "x| + foo(a, b) + y + z")
    expect_token("x", "x |+ foo(a, b) + y + z")
    expect_token("x", "x +| foo(a, b) + y + z")
    expect_token("foo", "x + |foo(a, b) + y + z")
    expect_token("a", "x + foo(|a, b) + y + z")
    expect_token("foo", "x + foo(a|, b) + y + z")
    expect_token("foo", "x + foo(a, b)| + y + z")
    expect_token("foo", "x + foo(a, b) |+ y + z")
    expect_token("foo", "x + foo(a, b) +| y + z")
    expect_token("y", "x + foo(a, b) + |y + z")
    expect_token("y", "x + foo(a, b) + y| + z")
    expect_token("y", "x + foo(a, b) + y |+ z")
    expect_token("y", "x + foo(a, b) + y +| z")
    expect_token("z", "x + foo(a, b) + y + |z")


def test_attrs():
    cell = "a = obj.attr.subattr"
    expected = "obj"
    idx = cell.find("obj") + 1
    for i in range(idx, idx + 3):
        expect_token(expected, cell, i)
    idx = cell.find(".attr") + 2
    expected = "obj.attr"
    for i in range(idx, idx + 4):
        expect_token(expected, cell, i)
    idx = cell.find(".subattr") + 2
    expected = "obj.attr.subattr"
    for i in range(idx, len(cell)):
        expect_token(expected, cell, i)


def test_line_at_cursor():
    cell = ""
    (line, offset) = line_at_cursor(cell, cursor_pos=11)
    assert line == ""
    assert offset == 0

    # The position after a newline should be the start of the following line.
    cell = "One\nTwo\n"
    (line, offset) = line_at_cursor(cell, cursor_pos=4)
    assert line == "Two\n"
    assert offset == 4

    # The end of a cell should be on the last line
    cell = "pri\npri"
    (line, offset) = line_at_cursor(cell, cursor_pos=7)
    assert line == "pri"
    assert offset == 4


@pytest.mark.parametrize(
    "c, token",
    zip(
        list(range(16, 22)) + list(range(22, 28)),
        ["int"] * (22 - 16) + ["map"] * (28 - 22),
    ),
)
def test_multiline_statement(c, token):
    cell = """a = (1,
    3)

int()
map()
"""
    expect_token(token, cell, c)
