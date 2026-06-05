"""Tests for various magic functions specific to the terminal frontend."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import sys
from io import StringIO

import pytest

from IPython.testing import tools as tt

# -----------------------------------------------------------------------------
# Test functions begin
# -----------------------------------------------------------------------------


MINIMAL_LAZY_MAGIC = """
from IPython.core.magic import (
    Magics,
    magics_class,
    line_magic,
    cell_magic,
)


@magics_class
class LazyMagics(Magics):
    @line_magic
    def lazy_line(self, line):
        print("Lazy Line")

    @cell_magic
    def lazy_cell(self, line, cell):
        print("Lazy Cell")


def load_ipython_extension(ipython):
    ipython.register_magics(LazyMagics)
"""


def check_cpaste(code, should_fail=False):
    """Execute code via 'cpaste' and ensure it was executed, unless
    should_fail is set.
    """
    ip.user_ns["code_ran"] = False

    src = StringIO()
    src.write(code)
    src.write("\n--\n")
    src.seek(0)

    stdin_save = sys.stdin
    sys.stdin = src

    try:
        context = tt.AssertPrints if should_fail else tt.AssertNotPrints
        with context("Traceback (most recent call last)"):
            ip.run_line_magic("cpaste", "")

        if not should_fail:
            assert ip.user_ns["code_ran"], "%r failed" % code
    finally:
        sys.stdin = stdin_save


def test_cpaste():
    """Test cpaste magic"""

    def runf():
        """Marker function: sets a flag when executed."""
        ip.user_ns["code_ran"] = True
        return "runf"  # return string so '+ runf()' doesn't result in success

    tests = {
        "pass": [
            "runf()",
            "In [1]: runf()",
            "In [1]: if 1:\n   ...:     runf()",
            "> > > runf()",
            ">>> runf()",
            "   >>> runf()",
        ],
        "fail": [
            "1 + runf()",
            "++ runf()",
        ],
    }

    ip.user_ns["runf"] = runf

    for code in tests["pass"]:
        check_cpaste(code)

    for code in tests["fail"]:
        check_cpaste(code, should_fail=True)


@pytest.fixture
def clipboard(monkeypatch):
    """Fixture that injects a fake clipboard hook and restores the original."""
    original_clip = ip.hooks.clipboard_get

    def paste(txt, flags="-q"):
        ip.hooks.clipboard_get = lambda: txt
        ip.run_line_magic("paste", flags)

    yield paste

    ip.hooks.clipboard_get = original_clip


def test_paste(clipboard):
    ip.user_ns.pop("x", None)
    clipboard("x = 1")
    assert ip.user_ns["x"] == 1
    ip.user_ns.pop("x")


def test_paste_pyprompt(clipboard):
    ip.user_ns.pop("x", None)
    clipboard(">>> x=2")
    assert ip.user_ns["x"] == 2
    ip.user_ns.pop("x")


def test_paste_py_multi(clipboard):
    clipboard(
        """
    >>> x = [1,2,3]
    >>> y = []
    >>> for i in x:
    ...     y.append(i**2)
    ...
    """
    )
    assert ip.user_ns["x"] == [1, 2, 3]
    assert ip.user_ns["y"] == [1, 4, 9]


def test_paste_py_multi_r(clipboard):
    "Test that paste -r works"
    test_paste_py_multi(clipboard)
    assert ip.user_ns.pop("x") == [1, 2, 3]
    assert ip.user_ns.pop("y") == [1, 4, 9]
    assert "x" not in ip.user_ns
    ip.run_line_magic("paste", "-r")
    assert ip.user_ns["x"] == [1, 2, 3]
    assert ip.user_ns["y"] == [1, 4, 9]


def test_paste_email(clipboard):
    "Test pasting of email-quoted contents"
    clipboard(
        """\
    >> def foo(x):
    >>     return x + 1
    >> xx = foo(1.1)"""
    )
    assert ip.user_ns["xx"] == 2.1


def test_paste_email2(clipboard):
    "Email again; some programs add a space also at each quoting level"
    clipboard(
        """\
    > > def foo(x):
    > >     return x + 1
    > > yy = foo(2.1)     """
    )
    assert ip.user_ns["yy"] == 3.1


def test_paste_email_py(clipboard):
    "Email quoting of interactive input"
    clipboard(
        """\
    >> >>> def f(x):
    >> ...   return x+1
    >> ...
    >> >>> zz = f(2.5)      """
    )
    assert ip.user_ns["zz"] == 3.5


def test_paste_echo(clipboard):
    "Test paste echoing, by temporarily faking the writer"
    w = StringIO()
    old_write = sys.stdout.write
    sys.stdout.write = w.write
    code = """
    a = 100
    b = 200"""
    try:
        clipboard(code, "")
        out = w.getvalue()
    finally:
        sys.stdout.write = old_write
    assert ip.user_ns["a"] == 100
    assert ip.user_ns["b"] == 200
    assert out == code + "\n## -- End pasted text --\n"


def test_paste_leading_commas():
    "Test multiline strings with leading commas"
    tm = ip.magics_manager.registry["TerminalMagics"]
    s = '''\
a = """
,1,2,3
"""'''
    ip.user_ns.pop("foo", None)
    tm.store_or_execute(s, "foo")
    assert "foo" in ip.user_ns


def test_paste_trailing_question(clipboard):
    "Test pasting sources with trailing question marks"
    tm = ip.magics_manager.registry["TerminalMagics"]
    s = """\
def funcfoo():
   if True: #am i true?
       return 'fooresult'
"""
    ip.user_ns.pop("funcfoo", None)
    clipboard(s)
    assert ip.user_ns["funcfoo"]() == "fooresult"
