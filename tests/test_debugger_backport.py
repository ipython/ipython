"""Tests for IPython.core.debugger_backport.

``PdbClosureBackport`` is a backport of the CPython 3.13 pdb changes making
closures work in the debugger (gh-83151).  It is mixed into
``IPython.core.debugger.Pdb`` on Python < 3.13 only, so the tests going
through ``Pdb`` commands are skipped on newer versions, while the
``_exec_in_closure`` unit tests always run.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import io
import sys

import pytest

from IPython.core import debugger
from IPython.core.debugger_backport import PdbClosureBackport

backport_in_use = pytest.mark.skipif(
    sys.version_info >= (3, 13),
    reason="the closure backport is only used on Python < 3.13",
)


class _FakeInput:
    """Fake stdin feeding predefined lines to the debugger."""

    def __init__(self, lines):
        self.lines = iter(lines)

    def readline(self):
        line = next(self.lines)
        print(line)
        return line + "\n"


def _post_mortem_pdb():
    """Return a Pdb instance set up post-mortem on a small traceback."""

    def fail():
        value = 3
        raise ValueError("backport-boom %s" % value)

    try:
        fail()
    except ValueError as exc:
        err = exc

    p = debugger.Pdb(stdout=io.StringIO(), readrc=False)
    p.set_theme_name("nocolor")
    p.reset()
    p.setup(None, err.__traceback__)
    assert p.curframe_locals["value"] == 3
    return p


# -----------------------------------------------------------------------------
# _exec_in_closure unit tests (run on every Python version)
# -----------------------------------------------------------------------------


def test_exec_in_closure_returns_false_for_flat_source():
    # no nested code object: the caller should fall back to a plain exec
    ns = {"x": 1}
    assert PdbClosureBackport()._exec_in_closure("x + 1", {}, ns) is False


def test_exec_in_closure_prints_expression_result(capsys):
    ns = {"x": 2}
    assert (
        PdbClosureBackport()._exec_in_closure(
            "sum(x * i for i in range(3))", {}, ns
        )
        is True
    )
    assert "6" in capsys.readouterr().out


def test_exec_in_closure_none_result_is_not_printed(capsys):
    ns = {"x": 2}
    assert PdbClosureBackport()._exec_in_closure("(lambda: None)()", {}, ns) is True
    assert "None" not in capsys.readouterr().out


def test_exec_in_closure_writes_locals_back():
    ns = {"x": 5}
    src = "def f_local():\n    return x\nresult = f_local()"
    assert PdbClosureBackport()._exec_in_closure(src, {}, ns) is True
    assert ns["result"] == 5
    assert "f_local" in ns
    # the internal evaluation scaffolding must not leak into the locals
    assert "__pdb_eval__" not in ns


def test_exec_in_closure_bad_local_names_fall_back():
    # "a-b" is not a valid identifier: building the closure source fails
    # and the method reports False so a plain exec is used instead
    assert (
        PdbClosureBackport()._exec_in_closure(
            "def f():\n    return 1\nf()", {}, {"a-b": 1}
        )
        is False
    )


def test_exec_in_closure_error_in_code_falls_back():
    src = "def f():\n    raise ValueError('inner-err')\nf()"
    assert PdbClosureBackport()._exec_in_closure(src, {}, {"x": 1}) is False


# -----------------------------------------------------------------------------
# default() through IPython's Pdb (only on Python versions using the backport)
# -----------------------------------------------------------------------------


@backport_in_use
def test_default_executes_expressions():
    p = _post_mortem_pdb()
    p.onecmd("value + 1")
    assert "4" in p.stdout.getvalue()


@backport_in_use
def test_default_strips_bang_prefix():
    p = _post_mortem_pdb()
    p.onecmd("!value * 10")
    assert "30" in p.stdout.getvalue()


@backport_in_use
def test_default_closure_expression():
    p = _post_mortem_pdb()
    # a generator expression needs the closure machinery to see `value`;
    # default() redirects sys.stdout to the debugger stdout while executing
    p.onecmd("sum(value * i for i in range(3))")
    assert "9" in p.stdout.getvalue()


@backport_in_use
def test_default_assignment_updates_locals():
    p = _post_mortem_pdb()
    p.onecmd("squares = [i * i for i in range(4)]")
    assert p.curframe_locals["squares"] == [0, 1, 4, 9]
    p.onecmd("squares")
    assert "[0, 1, 4, 9]" in p.stdout.getvalue()


@backport_in_use
def test_default_reports_errors():
    p = _post_mortem_pdb()
    p.onecmd("undefined_name_xyz")
    out = p.stdout.getvalue()
    assert "***" in out
    assert "NameError" in out


@backport_in_use
def test_default_multiline_command():
    # The multi-line code path of the backported default() relies on
    # pdb._disable_command_completion which only exists on Python >= 3.13,
    # so on the versions actually using the backport it reports an error
    # instead of silently hanging.
    p = _post_mortem_pdb()
    p.stdin = _FakeInput(["    y = 1", ""])
    p.use_rawinput = False
    p.onecmd("if True:")
    out = p.stdout.getvalue()
    assert "***" in out
    assert "AttributeError" in out
