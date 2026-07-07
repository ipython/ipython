"""Tests for IPython.terminal.ptutils."""

import os
import sys

import pytest
from unittest.mock import Mock, patch

from prompt_toolkit.document import Document

from IPython.core.completer import provisionalcompleter
from IPython.terminal.ptutils import (
    IPythonPTCompleter,
    IPythonPTLexer,
    _adjust_completion_text_based_on_context,
    _elide,
    _elide_point,
    _elide_typed,
)

ELLIPSIS = "\N{HORIZONTAL ELLIPSIS}"
TWO_DOT_LEADER = "\N{TWO DOT LEADER}"


# -----------------------------------------------------------------------------
# eliding helpers
# -----------------------------------------------------------------------------


def test_elide_point_disabled():
    long_string = "aaaaaaaaaa.bbbbbbbbbb.cccccccccc.dddddddddd"
    assert _elide_point(long_string, min_elide=0) == long_string
    assert _elide_point(long_string, min_elide=-1) == long_string


def test_elide_point_short_string():
    assert _elide_point("a.b.c.d", min_elide=30) == "a.b.c.d"


def test_elide_point_consecutive_dots():
    # three consecutive dots become a horizontal ellipsis,
    # two consecutive dots become a two dot leader
    assert _elide_point("a...b", min_elide=30) == f"a{ELLIPSIS}b"
    assert _elide_point("a..b", min_elide=30) == f"a{TWO_DOT_LEADER}b"


def test_elide_point_dotted_object():
    elided = _elide_point(
        "aaaaaaaaaa.bbbbbbbbbb.cccccccccc.dddddddddd", min_elide=30
    )
    assert elided == f"aaaaaaaaaa.b{ELLIPSIS}c.dddddddddd"


def test_elide_point_file_path():
    parts = ["aaaaaaaaaa", "bbbbbbbbbb", "cccccccccc", "dddddddddd"]
    path = os.sep.join(parts)
    elided = _elide_point(path, min_elide=30)
    assert elided == f"aaaaaaaaaa{os.sep}b{ELLIPSIS}c{os.sep}dddddddddd"
    # a trailing separator is ignored
    assert _elide_point(path + os.sep, min_elide=30) == elided


def test_elide_typed():
    string = "a" * 40
    typed = "a" * 15
    assert _elide_typed(string, typed, min_elide=30) == f"aaa{ELLIPSIS}" + "a" * 28
    # disabled
    assert _elide_typed(string, typed, min_elide=0) == string
    # string too short to elide
    assert _elide_typed("short", "short", min_elide=30) == "short"
    # typed prefix too short to be worth cutting
    assert _elide_typed(string, "aaa", min_elide=30) == string
    # string does not start with what was typed
    assert _elide_typed(string, "b" * 15, min_elide=30) == string


def test_elide_combined():
    string = "a" * 40
    assert _elide(string, "a" * 15, min_elide=30) == f"aaa{ELLIPSIS}" + "a" * 28
    assert _elide("a.b.c.d", "", min_elide=30) == "a.b.c.d"


# -----------------------------------------------------------------------------
# completion text adjustment
# -----------------------------------------------------------------------------


def test_adjust_completion_text_based_on_context():
    # a trailing '=' is dropped when the next char in the body is already '='
    assert _adjust_completion_text_based_on_context("n=", "f(n=)", 3) == "n"
    # otherwise the text is unchanged
    assert _adjust_completion_text_based_on_context("n=", "f(n)", 3) == "n="
    assert _adjust_completion_text_based_on_context("n", "f(n=)", 3) == "n"
    # offset past the end of the body
    assert _adjust_completion_text_based_on_context("n=", "f(n=", 5) == "n="


# -----------------------------------------------------------------------------
# IPythonPTCompleter
# -----------------------------------------------------------------------------


def test_pt_completer_requires_shell_or_completer():
    with pytest.raises(TypeError):
        IPythonPTCompleter()


def test_pt_completer_ipy_completer_property():
    ip = get_ipython()
    from_shell = IPythonPTCompleter(shell=ip)
    assert from_shell.ipy_completer is ip.Completer

    sentinel = object()
    explicit = IPythonPTCompleter(ipy_completer=sentinel)
    assert explicit.ipy_completer is sentinel


def test_pt_completer_empty_line_yields_nothing():
    ip = get_ipython()
    completer = IPythonPTCompleter(shell=ip)
    assert list(completer.get_completions(Document("", 0), Mock())) == []
    assert list(completer.get_completions(Document("   ", 3), Mock())) == []


def test_pt_completer_completes_print(monkeypatch):
    ip = get_ipython()
    # function-signature display ('print()') needs jedi; earlier tests may
    # have flipped use_jedi off on the session-wide shell.
    monkeypatch.setattr(ip.Completer, "use_jedi", True)
    completer = IPythonPTCompleter(shell=ip)
    completions = list(completer.get_completions(Document("pri", 3), Mock()))
    texts = [c.text for c in completions]
    assert "print" in texts

    printc = completions[texts.index("print")]
    assert printc.start_position == -3
    # 'print' is a function: display gets parentheses, meta shows the type
    assert printc.display[0][1] == "print()"
    assert printc.display_meta[0][1].startswith("function")


def test_pt_completer_non_function_completion():
    ip = get_ipython()
    ip.user_ns["some_test_variable"] = 42
    try:
        completer = IPythonPTCompleter(shell=ip)
        document = Document("some_test_var", 13)
        completions = list(completer.get_completions(document, Mock()))
        texts = [c.text for c in completions]
        assert "some_test_variable" in texts
        completion = completions[texts.index("some_test_variable")]
        # not a function: display has no added parentheses
        assert completion.display[0][1] == "some_test_variable"
    finally:
        del ip.user_ns["some_test_variable"]


def test_pt_completer_swallows_errors():
    class BadCompleter:
        def completions(self, body, offset):
            raise ValueError("boom")

    completer = IPythonPTCompleter(ipy_completer=BadCompleter())
    with patch("IPython.terminal.ptutils.traceback") as mock_traceback:
        assert list(completer.get_completions(Document("x", 1), Mock())) == []
    # the traceback is printed rather than propagated
    mock_traceback.print_exception.assert_called_once()
    assert isinstance(mock_traceback.print_exception.call_args[0][1], ValueError)


def test_pt_completer_skips_empty_text():
    class EmptyCompletion:
        text = ""
        start = 0
        end = 0
        type = "magic"
        signature = ""

    class EmptyCompleter:
        def completions(self, body, offset):
            yield EmptyCompletion()

    completer = IPythonPTCompleter(ipy_completer=EmptyCompleter())
    with provisionalcompleter():
        assert list(completer._get_completions("x", 1, 1, EmptyCompleter())) == []


def test_pt_completer_zero_width_character():
    # completing '\dot' yields a combining character of zero display width
    ip = get_ipython()
    completer = IPythonPTCompleter(shell=ip)
    body = "a\\dot"
    with provisionalcompleter():
        completions = list(
            completer._get_completions(body, len(body), len(body), ip.Completer)
        )
    assert len(completions) == 1
    assert completions[0].text == "\N{COMBINING DOT ABOVE}"


# -----------------------------------------------------------------------------
# IPythonPTLexer
# -----------------------------------------------------------------------------


@pytest.fixture
def spy_lexer():
    lexer = IPythonPTLexer()
    lexer.python_lexer = Mock()
    lexer.shell_lexer = Mock()
    lexer.magic_lexers = {name: Mock() for name in lexer.magic_lexers}
    return lexer


@pytest.mark.parametrize(
    "text, expected",
    [
        ("print(1)", "python"),
        ("", "python"),
        ("!ls", "shell"),
        ("%%bash\nls", "shell"),
        ("  !ls", "shell"),  # leading whitespace is stripped
        ("%%html\n<b>hi</b>", "html"),
        ("%%HTML\n<b>hi</b>", "HTML"),
        ("%%javascript\nvar x;", "javascript"),
        ("%%js\nvar x;", "js"),
        ("%%perl\nprint", "perl"),
        ("%%ruby\nputs", "ruby"),
        ("%%latex\n\\alpha", "latex"),
        ("%%unknownmagic\nfoo", "python"),  # unknown cell magic falls back
    ],
)
def test_lexer_dispatch(spy_lexer, text, expected):
    document = Document(text, 0)
    spy_lexer.lex_document(document)

    if expected == "python":
        chosen = spy_lexer.python_lexer
    elif expected == "shell":
        chosen = spy_lexer.shell_lexer
    else:
        chosen = spy_lexer.magic_lexers[expected]

    chosen.lex_document.assert_called_once_with(document)
    all_lexers = [
        spy_lexer.python_lexer,
        spy_lexer.shell_lexer,
        *spy_lexer.magic_lexers.values(),
    ]
    assert sum(l.lex_document.called for l in all_lexers) == 1


def test_lexer_lex_document_returns_callable():
    lexer = IPythonPTLexer()
    get_line = lexer.lex_document(Document("print(1)", 0))
    tokens = get_line(0)
    assert "".join(fragment for _, fragment in tokens) == "print(1)"
