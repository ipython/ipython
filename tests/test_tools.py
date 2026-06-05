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
import unittest

import pytest

from IPython.testing import decorators as dec
from IPython.testing import tools as tt


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


class Test_ipexec_validate(tt.TempFileMixin):
    def test_main_path(self):
        """Test with only stdout results."""
        self.mktmp("print('A')\n" "print('B')\n")
        out = "A\nB"
        tt.ipexec_validate(self.fname, out)

    def test_main_path2(self):
        """Test with only stdout results, expecting windows line endings."""
        self.mktmp("print('A')\n" "print('B')\n")
        out = "A\r\nB"
        tt.ipexec_validate(self.fname, out)

    def test_exception_path(self):
        """Test exception path in exception_validate."""
        self.mktmp(
            "import sys\n"
            "print('A')\n"
            "print('B')\n"
            "print('C', file=sys.stderr)\n"
            "print('D', file=sys.stderr)\n"
        )
        out = "A\nB"
        tt.ipexec_validate(self.fname, expected_out=out, expected_err="C\nD")

    def test_exception_path2(self):
        """Test exception path in exception_validate, expecting windows line endings."""
        self.mktmp(
            "import sys\n"
            "print('A')\n"
            "print('B')\n"
            "print('C', file=sys.stderr)\n"
            "print('D', file=sys.stderr)\n"
        )
        out = "A\r\nB"
        tt.ipexec_validate(self.fname, expected_out=out, expected_err="C\r\nD")

    def tearDown(self):
        # tear down correctly the mixin,
        # unittest.TestCase.tearDown does nothing
        tt.TempFileMixin.tearDown(self)
