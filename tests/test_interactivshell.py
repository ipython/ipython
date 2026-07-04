# -*- coding: utf-8 -*-
"""Tests for the TerminalInteractiveShell and related pieces."""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import unittest
import os
from types import SimpleNamespace

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


from IPython.testing import tools as tt

from IPython.terminal.ptutils import (
    IPythonPTCompleter,
    _adjust_completion_text_based_on_context,
    _elide,
)
from IPython.terminal.shortcuts.auto_suggest import NavigableAutoSuggestFromHistory


class TestAutoSuggest(unittest.TestCase):
    def test_changing_provider(self):
        ip = get_ipython()
        ip.autosuggestions_provider = None
        self.assertEqual(ip.auto_suggest, None)
        ip.autosuggestions_provider = "AutoSuggestFromHistory"
        self.assertIsInstance(ip.auto_suggest, AutoSuggestFromHistory)
        ip.autosuggestions_provider = "NavigableAutoSuggestFromHistory"
        self.assertIsInstance(ip.auto_suggest, NavigableAutoSuggestFromHistory)


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


class TestContextAwareCompletion(unittest.TestCase):
    def test_adjust_completion_text_based_on_context(self):
        # Adjusted case
        self.assertEqual(
            _adjust_completion_text_based_on_context("arg1=", "func1(a=)", 7), "arg1"
        )

        # Untouched cases
        self.assertEqual(
            _adjust_completion_text_based_on_context("arg1=", "func1(a)", 7), "arg1="
        )
        self.assertEqual(
            _adjust_completion_text_based_on_context("arg1=", "func1(a", 7), "arg1="
        )
        self.assertEqual(
            _adjust_completion_text_based_on_context("%magic", "func1(a=)", 7), "%magic"
        )
        self.assertEqual(
            _adjust_completion_text_based_on_context("func2", "func1(a=)", 7), "func2"
        )


class DummyCompleter:
    debug = False

    def __init__(self, completions=()):
        self._completions = completions

    def completions(self, body, offset):
        return self._completions


def test_postfix_prompt_toolkit_completions():
    ip = get_ipython()
    old_enabled = ip.postfix_completion
    old_style = ip.postfix_completion_style
    old_selected_style = ip.postfix_completion_selected_style
    try:
        ip.postfix_completion = True
        ip.postfix_completion_style = "bg:#111111 #eeeeee"
        ip.postfix_completion_selected_style = "bg:#222222 #ffffff"
        completer = IPythonPTCompleter(shell=ip)

        completions = list(
            completer._get_completions(
                "x.pri", len("x.pri"), len("x.pri"), DummyCompleter()
            )
        )

        assert len(completions) == 1
        assert completions[0].text == "print(x)"
        assert completions[0].start_position == -len("x.pri")
        assert completions[0].display_text == "print"
        assert completions[0].display_meta_text == "postfix"
        assert completions[0].style == "bg:#111111 #eeeeee"
        assert completions[0].selected_style == "bg:#222222 #ffffff"
    finally:
        ip.postfix_completion = old_enabled
        ip.postfix_completion_style = old_style
        ip.postfix_completion_selected_style = old_selected_style


def test_postfix_prompt_toolkit_completions_follow_normal_completions():
    ip = get_ipython()
    old_enabled = ip.postfix_completion
    try:
        ip.postfix_completion = True
        completer = IPythonPTCompleter(shell=ip)
        normal = SimpleNamespace(
            start=2,
            end=5,
            text="private",
            type="instance",
            signature="",
        )

        completions = list(
            completer._get_completions(
                "x.pri", len("x.pri"), len("x.pri"), DummyCompleter([normal])
            )
        )

        assert [completion.text for completion in completions] == [
            "private",
            "print(x)",
        ]
    finally:
        ip.postfix_completion = old_enabled


def test_postfix_prompt_toolkit_completions_disabled():
    ip = get_ipython()
    old_enabled = ip.postfix_completion
    try:
        ip.postfix_completion = False
        completer = IPythonPTCompleter(shell=ip)

        completions = list(
            completer._get_completions(
                "x.pri", len("x.pri"), len("x.pri"), DummyCompleter()
            )
        )

        assert completions == []
    finally:
        ip.postfix_completion = old_enabled


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

    def test_method(self):
        testgen = testfunc(self)
        with mock_input_helper(testgen) as mih:
            mih.ip.interact()

        if mih.exception is not None:
            # Re-raise captured exception
            etype, value, tb = mih.exception
            import traceback

            traceback.print_tb(tb, file=sys.stdout)
            del tb  # Avoid reference loop
            raise value

    return test_method


# Test classes -----------------------------------------------------------------


class InteractiveShellTestCase(unittest.TestCase):
    def rl_hist_entries(self, rl, n):
        """Get last n readline history entries as a list"""
        return [
            rl.get_history_item(rl.get_current_history_length() - x)
            for x in range(n - 1, -1, -1)
        ]

    @mock_input
    def test_inputtransformer_syntaxerror(self):
        ip = get_ipython()
        ip.input_transformers_post.append(syntax_error_transformer)

        try:
            # raise Exception
            with tt.AssertPrints("4", suppress=False):
                yield "print(2*2)"

            with tt.AssertPrints("SyntaxError: input contains", suppress=False):
                yield "print(2345) # syntaxerror"

            with tt.AssertPrints("16", suppress=False):
                yield "print(4*4)"

        finally:
            ip.input_transformers_post.remove(syntax_error_transformer)

    def test_repl_not_plain_text(self):
        ip = get_ipython()
        formatter = ip.display_formatter
        assert formatter.active_types == ["text/plain"]

        # terminal may have arbitrary mimetype handler to open external viewer
        # or inline images.
        assert formatter.ipython_display_formatter.enabled

        class Test(object):
            def __repr__(self):
                return "<Test %i>" % id(self)

            def _repr_html_(self):
                return "<html>"

        # verify that HTML repr isn't computed
        obj = Test()
        data, _ = formatter.format(obj)
        self.assertEqual(data, {"text/plain": repr(obj)})

        class Test2(Test):
            def _ipython_display_(self):
                from IPython.display import display, HTML

                display(HTML("<custom>"))

        # verify that mimehandlers are called
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

        assert called == True


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


class TerminalMagicsTestCase(unittest.TestCase):
    def test_paste_magics_blankline(self):
        """Test that code with a blank line doesn't get split (gh-3246)."""
        ip = get_ipython()
        s = "def pasted_func(a):\n" "    b = a+1\n" "\n" "    return b"

        tm = ip.magics_manager.registry["TerminalMagics"]
        tm.store_or_execute(s, name=None)

        self.assertEqual(ip.user_ns["pasted_func"](54), 55)
