# encoding: utf-8
"""
Tests for testing.tools
"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

import os

import pytest

from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils.io import temp_pyfile


@dec.skip_win32
def test_full_path_posix():
    spath = "/foo/bar.py"
    result = tt.full_path(spath, ["a.txt", "b.txt"])
    assert result == ["/foo/a.txt", "/foo/b.txt"]
    spath = "/foo"
    result = tt.full_path(spath, ["a.txt", "b.txt"])
    assert result == ["/a.txt", "/b.txt"]
    result = tt.full_path(spath, ["a.txt"])
    assert result == ["/a.txt"]


@dec.skip_if_not_win32
def test_full_path_win32():
    spath = "c:\\foo\\bar.py"
    result = tt.full_path(spath, ["a.txt", "b.txt"])
    assert result == ["c:\\foo\\a.txt", "c:\\foo\\b.txt"]
    spath = "c:\\foo"
    result = tt.full_path(spath, ["a.txt", "b.txt"])
    assert result == ["c:\\a.txt", "c:\\b.txt"]
    result = tt.full_path(spath, ["a.txt"])
    assert result == ["c:\\a.txt"]


@pytest.mark.parametrize("txt,expected_nerr,expected_nfail", [
    ("FAILED (errors=1)", 1, 0),
    ("FAILED (failures=1)", 0, 1),
    ("FAILED (errors=1, failures=1)", 1, 1),
])
def test_parser(txt, expected_nerr, expected_nfail):
    nerr, nfail = tt.parse_test_output(txt)
    assert nerr == expected_nerr
    assert nfail == expected_nfail


def test_temp_pyfile():
    src = "pass\n"
    fname = tt.temp_pyfile(src)
    assert os.path.isfile(fname)
    with open(fname, encoding="utf-8") as fh2:
        src2 = fh2.read()
    assert src2 == src


def test_assert_prints_passing():
    with tt.AssertPrints("abc"):
        print("abcd")
        print("def")
        print(b"ghi")


def test_assert_prints_failing():
    def func():
        with tt.AssertPrints("abc"):
            print("acd")
            print("def")
            print(b"ghi")

    with pytest.raises(AssertionError):
        func()


@pytest.fixture
def ipexec_tmpfile():
    """Fixture providing a mktmp helper that creates and cleans up temp files."""
    import os
    created = []

    def mktmp(src, ext=".py"):
        fname = temp_pyfile(src, ext)
        created.append(fname)
        return fname

    yield mktmp

    for fname in created:
        try:
            os.unlink(fname)
        except OSError:
            pass


def test_ipexec_validate_main_path(ipexec_tmpfile):
    """Test with only stdout results."""
    fname = ipexec_tmpfile("print('A')\n" "print('B')\n")
    tt.ipexec_validate(fname, "A\nB")


def test_ipexec_validate_main_path2(ipexec_tmpfile):
    """Test with only stdout results, expecting windows line endings."""
    fname = ipexec_tmpfile("print('A')\n" "print('B')\n")
    tt.ipexec_validate(fname, "A\r\nB")


def test_ipexec_validate_exception_path(ipexec_tmpfile):
    """Test exception path in exception_validate."""
    fname = ipexec_tmpfile(
        "import sys\n"
        "print('A')\n"
        "print('B')\n"
        "print('C', file=sys.stderr)\n"
        "print('D', file=sys.stderr)\n"
    )
    tt.ipexec_validate(fname, expected_out="A\nB", expected_err="C\nD")


def test_ipexec_validate_exception_path2(ipexec_tmpfile):
    """Test exception path in exception_validate, expecting windows line endings."""
    fname = ipexec_tmpfile(
        "import sys\n"
        "print('A')\n"
        "print('B')\n"
        "print('C', file=sys.stderr)\n"
        "print('D', file=sys.stderr)\n"
    )
    tt.ipexec_validate(fname, expected_out="A\r\nB", expected_err="C\r\nD")
