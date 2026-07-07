# -----------------------------------------------------------------------------
#  Copyright (C) 2010-2011 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------
import importlib.util
import io
import os
import sys

try:
    import curses
    import termios
except ImportError:
    # not available on Windows
    curses = None
    termios = None

import pytest

from IPython.testing.decorators import skip_win32

# N.B. For the test suite, page.pager_page is overridden (see tests/conftest.py)
from IPython.core import page
from IPython.core.error import TryNext


@pytest.fixture
def page_mod():
    """Load a pristine copy of IPython.core.page.

    The test-suite conftest replaces ``page.pager_page`` with a no-op at
    import time, so tests that exercise the real ``pager_page``/``page``
    implementations need an unmodified module instance.
    """
    spec = importlib.util.spec_from_file_location(
        "_ipython_core_page_under_test", page.__file__
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_detect_screen_size():
    """Simple smoketest for page._detect_screen_size."""
    try:
        page._detect_screen_size(True, 25)
    except (TypeError, io.UnsupportedOperation):
        # This can happen in the test suite, because stdout may not have a
        # fileno.
        pass


# -----------------------------------------------------------------------------
# display_page / as_hook
# -----------------------------------------------------------------------------


def test_display_page_string(monkeypatch):
    calls = []
    monkeypatch.setattr(page, "display", lambda data, raw: calls.append((data, raw)))
    page.display_page("a\nb\nc", start=1)
    assert calls == [({"text/plain": "b\nc"}, True)]


def test_display_page_string_no_start(monkeypatch):
    calls = []
    monkeypatch.setattr(page, "display", lambda data, raw: calls.append((data, raw)))
    page.display_page("hello")
    assert calls == [({"text/plain": "hello"}, True)]


def test_display_page_dict(monkeypatch):
    calls = []
    monkeypatch.setattr(page, "display", lambda data, raw: calls.append((data, raw)))
    bundle = {"text/plain": "hi", "text/html": "<b>hi</b>"}
    page.display_page(bundle, start=3)
    # mime-bundles are passed through untouched; start is ignored
    assert calls == [(bundle, True)]


def test_as_hook_strips_self():
    recorded = {}

    def pager_func(*args, **kwargs):
        recorded["args"] = args
        recorded["kwargs"] = kwargs

    hook = page.as_hook(pager_func)
    hook("<self>", "text", start=2)
    assert recorded["args"] == ("text",)
    assert recorded["kwargs"] == {"start": 2}


# -----------------------------------------------------------------------------
# page_dumb
# -----------------------------------------------------------------------------


def test_page_dumb_single_screen(capsys):
    page.page_dumb("line1\nline2", screen_lines=25)
    assert capsys.readouterr().out == "line1" + os.linesep + "line2\n"


def test_page_dumb_dict_input(capsys):
    page.page_dumb({"text/plain": "from bundle"}, screen_lines=25)
    assert capsys.readouterr().out == "from bundle\n"


def test_page_dumb_start_offset(capsys):
    page.page_dumb("a\nb\nc", start=2, screen_lines=25)
    assert capsys.readouterr().out == "c\n"


def test_page_dumb_multiple_screens(monkeypatch, capsys):
    monkeypatch.setattr(page, "page_more", lambda: True)
    # 5 lines with screen_lines=3 -> screens of 2 lines each
    page.page_dumb("l1\nl2\nl3\nl4\nl5", screen_lines=3)
    out = capsys.readouterr().out
    for expected in ("l1", "l2", "l3", "l4", "l5"):
        assert expected in out


def test_page_dumb_quit(monkeypatch, capsys):
    monkeypatch.setattr(page, "page_more", lambda: False)
    page.page_dumb("l1\nl2\nl3\nl4\nl5", screen_lines=3)
    out = capsys.readouterr().out
    assert "l1" in out
    # user quit after the first screen
    assert "l3" not in out
    assert "l5" not in out


def test_page_dumb_repeats_ansi_escape(monkeypatch, capsys):
    monkeypatch.setattr(page, "page_more", lambda: True)
    red = "\x1b[31m"
    page.page_dumb(red + "l1\nl2\nl3\nl4\nl5", screen_lines=3)
    out = capsys.readouterr().out
    # the last escape sequence of a screen is replayed on the next one
    assert out.count(red) >= 2


# -----------------------------------------------------------------------------
# _detect_screen_size
# -----------------------------------------------------------------------------


def test_detect_screen_size_non_xterm(monkeypatch):
    monkeypatch.setenv("TERM", "dumb")
    assert page._detect_screen_size(42) == 42


def test_detect_screen_size_no_term(monkeypatch):
    monkeypatch.delenv("TERM", raising=False)
    assert page._detect_screen_size(13) == 13


def test_detect_screen_size_no_curses(monkeypatch):
    monkeypatch.setenv("TERM", "xterm")
    # a None entry in sys.modules makes `import curses` raise ImportError
    monkeypatch.setitem(sys.modules, "curses", None)
    assert page._detect_screen_size(42) == 42


@pytest.mark.skipif(termios is None, reason="requires termios")
def test_detect_screen_size_termios_error(monkeypatch):
    monkeypatch.setenv("TERM", "xterm")

    def raise_termios(fd):
        raise termios.error("simulated failure")

    monkeypatch.setattr(termios, "tcgetattr", raise_termios)
    with pytest.raises(TypeError, match="termios error"):
        page._detect_screen_size(42)


@pytest.mark.skipif(termios is None, reason="requires termios and curses")
def test_detect_screen_size_curses_incomplete(monkeypatch):
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setattr(termios, "tcgetattr", lambda fd: "flags")

    def raise_attr_error():
        raise AttributeError("no initscr")

    monkeypatch.setattr(curses, "initscr", raise_attr_error)
    assert page._detect_screen_size(42) == 42


@pytest.mark.skipif(termios is None, reason="requires termios and curses")
def test_detect_screen_size_success(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-color")
    monkeypatch.setattr(termios, "tcgetattr", lambda fd: "flags")
    restored = []
    monkeypatch.setattr(
        termios, "tcsetattr", lambda fd, when, flags: restored.append(flags)
    )

    class FakeScreen:
        def getmaxyx(self):
            return (48, 80)

    monkeypatch.setattr(curses, "initscr", FakeScreen)
    monkeypatch.setattr(curses, "endwin", lambda: None)
    assert page._detect_screen_size(42) == 48
    # terminal state must be restored unconditionally
    assert restored == ["flags"]


# -----------------------------------------------------------------------------
# pager_page (on a pristine module copy, see the page_mod fixture)
# -----------------------------------------------------------------------------


def test_pager_page_dumb_term_prints(page_mod, monkeypatch, capsys):
    monkeypatch.setenv("TERM", "dumb")
    page_mod.pager_page("some text")
    assert capsys.readouterr().out == "some text\n"


def test_pager_page_mime_bundle(page_mod, monkeypatch, capsys):
    monkeypatch.setenv("TERM", "dumb")
    page_mod.pager_page({"text/plain": "bundle text"})
    assert capsys.readouterr().out == "bundle text\n"


def test_pager_page_fits_on_screen(page_mod, monkeypatch, capsys):
    monkeypatch.setenv("TERM", "xterm")
    page_mod.pager_page("short\ntext", screen_lines=100)
    assert capsys.readouterr().out == "short" + os.linesep + "text\n"


def test_pager_page_start_offset(page_mod, monkeypatch, capsys):
    monkeypatch.setenv("TERM", "xterm")
    page_mod.pager_page("a\nb\nc", start=2, screen_lines=100)
    assert capsys.readouterr().out == "c\n"


def test_pager_page_detect_failure_prints(page_mod, monkeypatch, capsys):
    monkeypatch.setenv("TERM", "xterm")

    def raise_type_error(default):
        raise TypeError("no tty")

    monkeypatch.setattr(page_mod, "_detect_screen_size", raise_type_error)
    page_mod.pager_page("plain text", screen_lines=0)
    assert capsys.readouterr().out == "plain text\n"


@skip_win32
def test_pager_page_uses_pager(page_mod, monkeypatch):
    monkeypatch.setenv("TERM", "xterm")
    dumb_calls = []
    monkeypatch.setattr(
        page_mod, "page_dumb", lambda *a, **kw: dumb_calls.append((a, kw))
    )
    text = "\n".join("line %d" % i for i in range(50))
    page_mod.pager_page(text, screen_lines=10, pager_cmd="cat > /dev/null")
    # the pager consumed the text successfully: no dumb-pager fallback
    assert dumb_calls == []


@skip_win32
def test_pager_page_falls_back_to_page_dumb(page_mod, monkeypatch):
    monkeypatch.setenv("TERM", "xterm")
    dumb_calls = []
    monkeypatch.setattr(
        page_mod, "page_dumb", lambda strng, screen_lines: dumb_calls.append(strng)
    )
    text = "\n".join("line %d" % i for i in range(50))
    page_mod.pager_page(text, screen_lines=10, pager_cmd="cat > /dev/null; exit 3")
    assert dumb_calls == [text]


@skip_win32
def test_pager_page_broken_pipe(page_mod, monkeypatch):
    # a broken pipe means the user quit the pager: not an error
    monkeypatch.setenv("TERM", "xterm")
    dumb_calls = []
    monkeypatch.setattr(
        page_mod, "page_dumb", lambda *a, **kw: dumb_calls.append((a, kw))
    )

    def raise_broken_pipe(*args, **kwargs):
        raise OSError(32, "Broken pipe")

    monkeypatch.setattr(page_mod.subprocess, "Popen", raise_broken_pipe)
    text = "\n".join("line %d" % i for i in range(50))
    page_mod.pager_page(text, screen_lines=10, pager_cmd="cat > /dev/null")
    assert dumb_calls == []


@skip_win32
def test_pager_page_oserror_falls_back(page_mod, monkeypatch):
    monkeypatch.setenv("TERM", "xterm")
    dumb_calls = []
    monkeypatch.setattr(
        page_mod, "page_dumb", lambda strng, screen_lines: dumb_calls.append(strng)
    )

    def raise_oserror(*args, **kwargs):
        raise OSError("no such pager")

    monkeypatch.setattr(page_mod.subprocess, "Popen", raise_oserror)
    text = "\n".join("line %d" % i for i in range(50))
    page_mod.pager_page(text, screen_lines=10, pager_cmd="cat > /dev/null")
    assert dumb_calls == [text]


# -----------------------------------------------------------------------------
# page
# -----------------------------------------------------------------------------


def test_page_no_ipython_falls_back(page_mod, monkeypatch):
    calls = []
    monkeypatch.setattr(page_mod, "get_ipython", lambda: None)
    monkeypatch.setattr(
        page_mod, "pager_page", lambda *args: calls.append(args)
    )
    page_mod.page("text", start=-5)
    # negative start is clamped to 0
    assert calls == [("text", 0, 0, None)]


def test_page_uses_hook(page_mod, monkeypatch):
    hook_calls = []

    class FakeHooks:
        def show_in_pager(self, data, start, screen_lines):
            hook_calls.append((data, start, screen_lines))

    class FakeShell:
        hooks = FakeHooks()

    monkeypatch.setattr(page_mod, "get_ipython", lambda: FakeShell())
    monkeypatch.setattr(
        page_mod,
        "pager_page",
        lambda *args: pytest.fail("pager_page should not be called"),
    )
    page_mod.page("text", start=3, screen_lines=7)
    assert hook_calls == [("text", 3, 7)]


def test_page_hook_trynext_falls_back(page_mod, monkeypatch):
    calls = []

    class FakeHooks:
        def show_in_pager(self, data, start, screen_lines):
            raise TryNext()

    class FakeShell:
        hooks = FakeHooks()

    monkeypatch.setattr(page_mod, "get_ipython", lambda: FakeShell())
    monkeypatch.setattr(page_mod, "pager_page", lambda *args: calls.append(args))
    page_mod.page("text")
    assert calls == [("text", 0, 0, None)]


# -----------------------------------------------------------------------------
# page_file
# -----------------------------------------------------------------------------


def test_page_file_uses_system_pager(page_mod, monkeypatch, tmp_path):
    monkeypatch.setenv("TERM", "xterm")
    # keep 'less' unmodified by get_pager_cmd so get_pager_start matches it
    monkeypatch.setenv("LESS", "-r")
    commands = []
    monkeypatch.setattr(page_mod, "system", lambda cmd: commands.append(cmd))
    fname = tmp_path / "some_file.txt"
    fname.write_text("contents", encoding="utf-8")
    page_mod.page_file(str(fname), start=2, pager_cmd="less")
    assert commands == ["less +2 %s" % fname]


@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_page_file_fallback_to_page(page_mod, monkeypatch, tmp_path):
    # 'emacs' TERM forces the fallback to page()
    monkeypatch.setenv("TERM", "emacs")
    calls = []
    monkeypatch.setattr(page_mod, "page", lambda strng, start: calls.append((strng, start)))
    fname = tmp_path / "some_file.txt"
    fname.write_text("file contents", encoding="utf-8")
    page_mod.page_file(str(fname), start=2)
    # start is decremented by one for 0-based indexing
    assert calls == [("file contents", 1)]


def test_page_file_unreadable(page_mod, monkeypatch, capsys):
    monkeypatch.setenv("TERM", "emacs")
    page_mod.page_file("/nonexistent/no/such/file.txt")
    assert "Unable to show file" in capsys.readouterr().out


# -----------------------------------------------------------------------------
# get_pager_cmd / get_pager_start
# -----------------------------------------------------------------------------


@pytest.mark.skipif(os.name != "posix", reason="posix default pager")
def test_get_pager_cmd_default(monkeypatch):
    monkeypatch.delenv("PAGER", raising=False)
    assert page.get_pager_cmd() == "less -R"


def test_get_pager_cmd_from_env(monkeypatch):
    monkeypatch.setenv("PAGER", "more")
    assert page.get_pager_cmd() == "more"


def test_get_pager_cmd_explicit():
    assert page.get_pager_cmd("mypager") == "mypager"


def test_get_pager_cmd_less_gets_R_flag(monkeypatch):
    monkeypatch.delenv("LESS", raising=False)
    assert page.get_pager_cmd("less") == "less -R"


def test_get_pager_cmd_less_respects_LESS_env(monkeypatch):
    monkeypatch.setenv("LESS", "-r")
    assert page.get_pager_cmd("less") == "less"


def test_get_pager_start():
    assert page.get_pager_start("less", 3) == "+3"
    assert page.get_pager_start("more", 10) == "+10"
    assert page.get_pager_start("less", 0) == ""
    assert page.get_pager_start("cat", 3) == ""


# -----------------------------------------------------------------------------
# page_more
# -----------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="posix page_more uses input()")
@pytest.mark.parametrize(
    "answer,expected",
    [("", True), ("y", True), ("q", False), ("Quit", False)],
)
def test_page_more(monkeypatch, answer, expected):
    monkeypatch.setattr("builtins.input", lambda prompt: answer)
    assert page.page_more() is expected
