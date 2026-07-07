# coding: utf-8

import re

from IPython.core.oinspect import OInfo
from IPython.core.splitinput import split_user_input, LineInfo

import pytest

tests = [
    ("x=1", ("", "", "x", "=1")),
    ("?", ("", "?", "", "")),
    ("??", ("", "??", "", "")),
    (" ?", (" ", "?", "", "")),
    (" ??", (" ", "??", "", "")),
    ("??x", ("", "??", "x", "")),
    ("?x=1", ("", "?", "x", "=1")),
    ("!ls", ("", "!", "ls", "")),
    ("  !ls", ("  ", "!", "ls", "")),
    ("!!ls", ("", "!!", "ls", "")),
    ("  !!ls", ("  ", "!!", "ls", "")),
    (",ls", ("", ",", "ls", "")),
    (";ls", ("", ";", "ls", "")),
    ("  ;ls", ("  ", ";", "ls", "")),
    ("f.g(x)", ("", "", "f.g", "(x)")),
    ("f.g (x)", ("", "", "f.g", " (x)")),
    ("?%hist1", ("", "?", "%hist1", "")),
    ("?%%hist2", ("", "?", "%%hist2", "")),
    ("??%hist3", ("", "??", "%hist3", "")),
    ("??%%hist4", ("", "??", "%%hist4", "")),
    ("?x*", ("", "?", "x*", "")),
    ("Pérez Fernando", ("", "", "Pérez", " Fernando")),
]


@pytest.mark.parametrize("input, output", tests)
def test_split_user_input(input, output):
    assert split_user_input(input) == output


def test_LineInfo():
    """Simple test for LineInfo construction and str()"""
    linfo = LineInfo("  %cd /home")
    assert str(linfo) == "LineInfo [  |%|cd|/home]"


def test_LineInfo_repr():
    linfo = LineInfo("!ls -la")
    assert repr(linfo) == "<LineInfo [|!|ls|-la]>"


def test_LineInfo_attributes():
    linfo = LineInfo("  f(x)   # comment")
    assert linfo.line == "  f(x)   # comment"
    assert linfo.continue_prompt is False
    assert linfo.pre == "  "
    assert linfo.pre_char == ""
    assert linfo.pre_whitespace == "  "
    assert linfo.esc == ""
    assert linfo.ifun == "f"
    assert linfo.raw_the_rest == "(x)   # comment"
    assert linfo.the_rest == "(x)   # comment"


def test_LineInfo_continue_prompt():
    linfo = LineInfo("x = 1", continue_prompt=True)
    assert linfo.continue_prompt is True


def test_split_user_input_pattern_no_match():
    """When the pattern does not match, fall back to str.split."""
    no_match = re.compile(r"\Adoes-not-match\Z")
    assert split_user_input("ls -la", no_match) == ("", "", "ls", "-la")


def test_split_user_input_pattern_no_match_single_word():
    """Fallback when the line has no whitespace to split on."""
    no_match = re.compile(r"\Adoes-not-match\Z")
    assert split_user_input("ls", no_match) == ("", "", "ls", "")


def test_split_user_input_pattern_no_match_leading_space():
    no_match = re.compile(r"\Adoes-not-match\Z")
    assert split_user_input("   ls -la", no_match) == ("   ", "", "ls", "-la")


def test_LineInfo_ofind_deprecated():
    """LineInfo.ofind is deprecated but still delegates to shell._ofind."""
    linfo = LineInfo("len 3")
    with pytest.deprecated_call(match="LineInfo.ofind\\(\\) is deprecated"):
        info = linfo.ofind(ip)
    assert isinstance(info, OInfo)
    assert info.found is True
    assert info.obj is len
