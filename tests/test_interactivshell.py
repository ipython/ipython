# -*- coding: utf-8 -*-
"""Tests for the TerminalInteractiveShell and related pieces."""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import os

import pytest

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


from IPython.testing import tools as tt

from IPython.terminal.ptutils import _elide, _adjust_completion_text_based_on_context
from IPython.terminal.shortcuts.auto_suggest import NavigableAutoSuggestFromHistory


def test_changing_provider():
    ip = get_ipython()
    ip.autosuggestions_provider = None
    assert ip.auto_suggest is None
    ip.autosuggestions_provider = "AutoSuggestFromHistory"
    assert isinstance(ip.auto_suggest, AutoSuggestFromHistory)
    ip.autosuggestions_provider = "NavigableAutoSuggestFromHistory"
    assert isinstance(ip.auto_suggest, NavigableAutoSuggestFromHistory)


def test_elide():
    _elide("concatenate((a1, a2, ...), axis", "", min_elide=30)  # do not raise
    _elide("concatenate((a1, a2, ..), . axis", "", min_elide=30)  # do not raise
    assert (
        _elide("aaaa.bbbb.ccccc.dddddd.eeeee.fffff.gggggg.hhhhhh", "", min_elide=30)
        == "aaaa.b…g.hhhhhh"
    )

    test_string = os.sep.join(["", 10 * "a", 10 * "b", 10 * "c", ""])
    expect_string = os.sep + "a" + "\N{HORIZONTAL ELLIPSIS}" + "b" + os.sep + 10 * "c"
    assert _elide(test_string, "", min_elide=30) == expect_string


def test_elide_typed_normal():
    assert (
        _elide(
            "the quick brown fox jumped over the lazy dog",
            "the quick brown fox",
            min_elide=10,
        )
        == "the…fox jumped over the lazy dog"
    )


def test_elide_typed_short_match():
    """
    if the match is too short we don't elide.
    avoid the "the...the"
    """
    assert (
        _elide("the quick brown fox jumped over the lazy dog", "the", min_elide=10)
        == "the quick brown fox jumped over the lazy dog"
    )


def test_elide_typed_no_match():
    """
    if the match is too short we don't elide.
    avoid the "the...the"
    """
    # here we typed red instead of brown
    assert (
        _elide(
            "the quick brown fox jumped over the lazy dog",
            "the quick red fox",
            min_elide=10,
        )
        == "the quick brown fox jumped over the lazy dog"
    )


@pytest.mark.parametrize("completion,line_buffer,cursor_pos,expected", [
    ("arg1=", "func1(a=)", 7, "arg1"),    # adjusted: trailing = removed
    ("arg1=", "func1(a)", 7, "arg1="),    # untouched: no = in buffer
    ("arg1=", "func1(a", 7, "arg1="),     # untouched: no = in buffer
    ("%magic", "func1(a=)", 7, "%magic"), # untouched: magic completion
    ("func2", "func1(a=)", 7, "func2"),   # untouched: function name
])
def test_adjust_completion_text_based_on_context(completion, line_buffer, cursor_pos, expected):
    result = _adjust_completion_text_based_on_context(completion, line_buffer, cursor_pos)
    assert result == expected


# Decorator for interaction loop tests -----------------------------------------


class mock_input_helper(object):
    """Machinery for tests of the main interact loop.

    Used by the mock_input decorator.
    """

    def __init__(self, testgen):
        self.testgen = testgen
        self.exception = None
        self.ip = get_ipython()

    def __enter__(self):
        self.orig_prompt_for_code = self.ip.prompt_for_code
        self.ip.prompt_for_code = self.fake_input
        return self

    def __exit__(self, etype, value, tb):
        self.ip.prompt_for_code = self.orig_prompt_for_code

    def fake_input(self):
        try:
            return next(self.testgen)
        except StopIteration:
            self.ip.keep_running = False
            return ""
        except:
            self.exception = sys.exc_info()
            self.ip.keep_running = False
            return ""


def mock_input(testfunc):
    """Decorator for tests of the main interact loop.

    Write the test as a generator, yield-ing the input strings, which IPython
    will see as if they were typed in at the prompt.
    """

    def test_wrapper():
        testgen = testfunc()
        with mock_input_helper(testgen) as mih:
            mih.ip.interact()

        if mih.exception is not None:
            etype, value, tb = mih.exception
            import traceback

            traceback.print_tb(tb, file=sys.stdout)
            del tb
            raise value

    return test_wrapper


@mock_input
def test_inputtransformer_syntaxerror():
    ip = get_ipython()
    ip.input_transformers_post.append(syntax_error_transformer)

    try:
        with tt.AssertPrints("4", suppress=False):
            yield "print(2*2)"

        with tt.AssertPrints("SyntaxError: input contains", suppress=False):
            yield "print(2345) # syntaxerror"

        with tt.AssertPrints("16", suppress=False):
            yield "print(4*4)"

    finally:
        ip.input_transformers_post.remove(syntax_error_transformer)


def test_repl_not_plain_text():
    ip = get_ipython()
    formatter = ip.display_formatter
    assert formatter.active_types == ["text/plain"]

    assert formatter.ipython_display_formatter.enabled

    class Test(object):
        def __repr__(self):
            return "<Test %i>" % id(self)

        def _repr_html_(self):
            return "<html>"

    obj = Test()
    data, _ = formatter.format(obj)
    assert data == {"text/plain": repr(obj)}

    class Test2(Test):
        def _ipython_display_(self):
            from IPython.display import display, HTML

            display(HTML("<custom>"))

    called = False

    def handler(data, metadata):
        print("Handler called")
        nonlocal called
        called = True

    ip.display_formatter.active_types.append("text/html")
    ip.display_formatter.formatters["text/html"].enabled = True
    ip.mime_renderers["text/html"] = handler
    try:
        obj = Test()
        display(obj)
    finally:
        ip.display_formatter.formatters["text/html"].enabled = False
        del ip.mime_renderers["text/html"]

    assert called is True


def syntax_error_transformer(lines):
    """Transformer that throws SyntaxError if 'syntaxerror' is in the code."""
    for line in lines:
        pos = line.find("syntaxerror")
        if pos >= 0:
            e = SyntaxError('input contains "syntaxerror"')
            e.text = line
            e.offset = pos + 1
            raise e
    return lines


def test_paste_magics_blankline():
    """Test that code with a blank line doesn't get split (gh-3246)."""
    ip = get_ipython()
    s = "def pasted_func(a):\n" "    b = a+1\n" "\n" "    return b"

    tm = ip.magics_manager.registry["TerminalMagics"]
    tm.store_or_execute(s, name=None)

    assert ip.user_ns["pasted_func"](54) == 55
