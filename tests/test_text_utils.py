"""Parametrized tests for IPython.utils.text utility functions."""
import pytest
from IPython.utils.text import (
    indent,
    list_strings,
    marquee,
    format_screen,
    dedent,
    get_text_list,
)


# ---------------------------------------------------------------------------
# indent
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,nspaces,expected", [
    ("hello", 4, "    hello"),
    ("hello\nworld", 2, "  hello\n  world"),
    ("a\nb", 0, "a\nb"),
])
def test_indent_spaces(text, nspaces, expected):
    assert indent(text, nspaces=nspaces) == expected


def test_indent_tabs():
    result = indent("hello", ntabs=1, nspaces=0)
    assert result == "\thello"


def test_indent_flatten():
    text = "   already\n      indented"
    result = indent(text, nspaces=2, flatten=True)
    lines = result.splitlines()
    assert all(line.startswith("  ") for line in lines if line)
    # All lines should start with exactly the same indentation
    assert lines[0] == "  already"
    assert lines[1] == "  indented"


# ---------------------------------------------------------------------------
# list_strings
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("input_,expected", [
    ("single string", ["single string"]),
    (["already", "a", "list"], ["already", "a", "list"]),
    (["one"], ["one"]),
    ("", [""]),
])
def test_list_strings(input_, expected):
    assert list_strings(input_) == expected


def test_list_strings_returns_same_list_object():
    lst = ["a", "b"]
    assert list_strings(lst) is lst


# ---------------------------------------------------------------------------
# marquee
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("txt,width,mark,expected_contains", [
    ("test", 20, "*", "test"),
    ("", 10, "-", None),  # empty text: just marks
    ("hi", 14, "=", "hi"),
])
def test_marquee_contains_text(txt, width, mark, expected_contains):
    result = marquee(txt, width=width, mark=mark)
    if expected_contains:
        assert expected_contains in result
    else:
        assert mark in result


@pytest.mark.parametrize("width", [10, 20, 40, 78])
def test_marquee_empty_text_fills_width(width):
    result = marquee("", width=width)
    assert len(result) == width


def test_marquee_symmetric():
    result = marquee("A test", 40)
    text_pos = result.index("A test")
    left = result[:text_pos].strip()
    right = result[text_pos + len("A test"):].strip()
    assert left == right


# ---------------------------------------------------------------------------
# format_screen
# ---------------------------------------------------------------------------

def test_format_screen_removes_backslash_continuation():
    result = format_screen("line one\\\nline two")
    assert "\\" not in result


def test_format_screen_passthrough_plain():
    plain = "no special chars"
    assert format_screen(plain) == plain


# ---------------------------------------------------------------------------
# dedent
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    # Already clean
    ("hello", "hello"),
    # Starts with newline - full dedent applied (common indent stripped)
    ("\n    foo\n    bar", "\nfoo\nbar"),
    # First line unindented, rest indented - only the rest gets dedented
    ("first\n    second\n    third", "first\nsecond\nthird"),
    # Single line with indentation - textwrap.dedent strips it
    ("    indented", "indented"),
])
def test_dedent(text, expected):
    assert dedent(text) == expected


# ---------------------------------------------------------------------------
# get_text_list
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("items,last_sep,sep,wrap,expected", [
    ([], " and ", ", ", "", ""),
    (["a"], " and ", ", ", "", "a"),
    (["a", "b"], " and ", ", ", "", "a and b"),
    (["a", "b", "c"], " and ", ", ", "", "a, b and c"),
    (["a", "b", "c", "d"], " and ", ", ", "", "a, b, c and d"),
    (["a", "b", "c"], " or ", ", ", "", "a, b or c"),
    (["a", "b"], " and ", ", ", "`", "`a` and `b`"),
    (["a", "b", "c"], ", ", " + ", "", "a + b, c"),
])
def test_get_text_list(items, last_sep, sep, wrap, expected):
    result = get_text_list(items, last_sep=last_sep, sep=sep, wrap_item_with=wrap)
    assert result == expected
