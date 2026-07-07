"""Tests for IPython.utils.terminal."""

import importlib
import os

import pytest

from IPython.utils import terminal


@pytest.fixture
def reload_with_term():
    """Reload the terminal module with a given TERM, then restore it."""

    def reload(term_value):
        os.environ["TERM"] = term_value
        importlib.reload(terminal)
        return terminal

    orig_term = os.environ.get("TERM")
    yield reload
    if orig_term is None:
        os.environ.pop("TERM", None)
    else:
        os.environ["TERM"] = orig_term
    importlib.reload(terminal)


@pytest.fixture
def title_recorder(monkeypatch):
    """Record calls to the platform-specific title setters/restorers."""
    calls = []
    monkeypatch.setattr(
        terminal, "_set_term_title", lambda title: calls.append(("set", title))
    )
    monkeypatch.setattr(
        terminal, "_restore_term_title", lambda: calls.append(("restore",))
    )
    return calls


def test_toggle_set_term_title(monkeypatch):
    # ensure the module-level flag is restored after the test
    monkeypatch.setattr(terminal, "ignore_termtitle", True)
    terminal.toggle_set_term_title(True)
    assert terminal.ignore_termtitle is False
    terminal.toggle_set_term_title(False)
    assert terminal.ignore_termtitle is True


def test_set_term_title_ignored_by_default(monkeypatch, title_recorder):
    monkeypatch.setattr(terminal, "ignore_termtitle", True)
    terminal.set_term_title("a title")
    terminal.restore_term_title()
    assert title_recorder == []


def test_set_term_title_enabled(monkeypatch, title_recorder):
    monkeypatch.setattr(terminal, "ignore_termtitle", False)
    terminal.set_term_title("a title")
    terminal.restore_term_title()
    assert title_recorder == [("set", "a title"), ("restore",)]


def test_set_term_title_xterm_saves_once(monkeypatch, capsys):
    monkeypatch.setattr(terminal, "_xterm_term_title_saved", False)
    terminal._set_term_title_xterm("first")
    assert terminal._xterm_term_title_saved is True
    # first call pushes the current title onto the xterm title stack
    assert capsys.readouterr().out == "\033[22;0t\033]0;first\007"
    terminal._set_term_title_xterm("second")
    # subsequent calls only set the title, without saving again
    assert capsys.readouterr().out == "\033]0;second\007"


def test_restore_term_title_xterm(monkeypatch, capsys):
    monkeypatch.setattr(terminal, "_xterm_term_title_saved", True)
    terminal._restore_term_title_xterm()
    assert capsys.readouterr().out == "\033[23;0t"
    assert terminal._xterm_term_title_saved is False


def test_restore_term_title_xterm_without_save_warns(monkeypatch, capsys):
    monkeypatch.setattr(terminal, "_xterm_term_title_saved", False)
    with pytest.warns(UserWarning, match="will not restore terminal title"):
        terminal._restore_term_title_xterm()
    # nothing is written to the terminal
    assert capsys.readouterr().out == ""


def test_term_title_functions_bound_on_xterm(reload_with_term):
    mod = reload_with_term("xterm-256color")
    assert mod._set_term_title is mod._set_term_title_xterm
    assert mod._restore_term_title is mod._restore_term_title_xterm


def test_term_title_functions_noop_on_dumb_terminal(reload_with_term, capsys):
    mod = reload_with_term("dumb")
    assert mod._set_term_title is not mod._set_term_title_xterm
    assert mod._restore_term_title is not mod._restore_term_title_xterm
    # the fallbacks are no-ops that write nothing
    mod._set_term_title("a title")
    mod._restore_term_title()
    assert capsys.readouterr().out == ""


def test_term_clear(monkeypatch):
    commands = []
    monkeypatch.setattr(os, "system", commands.append)
    terminal._term_clear()
    # This test suite runs on posix systems only.
    assert commands == ["clear"]


def test_get_terminal_size_from_environment(monkeypatch):
    monkeypatch.setenv("COLUMNS", "120")
    monkeypatch.setenv("LINES", "43")
    assert terminal.get_terminal_size() == (120, 43)


def test_get_terminal_size_defaults(monkeypatch):
    # shutil.get_terminal_size falls back to the passed default values
    monkeypatch.setattr(terminal, "_get_terminal_size", lambda fallback: fallback)
    assert terminal.get_terminal_size() == (80, 25)
    assert terminal.get_terminal_size(100, 50) == (100, 50)
