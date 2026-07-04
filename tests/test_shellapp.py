# -*- coding: utf-8 -*-
"""Tests for shellapp module.

Authors
-------
* Bradley Froehle
"""
# -----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import subprocess
import sys
import unittest

from IPython.testing import decorators as dec
from IPython.testing import tools as tt


class TestFileToRun(tt.TempFileMixin, unittest.TestCase):
    """Test the behavior of the file_to_run parameter."""

    def test_py_script_file_attribute(self):
        """Test that `__file__` is set when running `ipython file.py`"""
        src = "print(__file__)\n"
        self.mktmp(src)

        err = None
        tt.ipexec_validate(self.fname, self.fname, err)

    def test_ipy_script_file_attribute(self):
        """Test that `__file__` is set when running `ipython file.ipy`"""
        src = "print(__file__)\n"
        self.mktmp(src, ext=".ipy")

        err = None
        tt.ipexec_validate(self.fname, self.fname, err)

    # The commands option to ipexec_validate doesn't work on Windows, and it
    # doesn't seem worth fixing
    @dec.skip_win32
    def test_py_script_file_attribute_interactively(self):
        """Test that `__file__` is not set after `ipython -i file.py`"""
        src = "True\n"
        self.mktmp(src)

        out, err = tt.ipexec(
            self.fname,
            options=["-i"],
            commands=['"__file__" in globals()', "print(123)", "exit()"],
        )
        assert "False" in out, f"Subprocess stderr:\n{err}\n-----"


class TestExitCode(tt.TempFileMixin, unittest.TestCase):
    """Test that IPython preserves exit codes from sys.exit()."""

    def _ipython_rc(self, *args):
        """Run IPython with given args and return the exit code."""
        cmd = [sys.executable, "-m", "IPython"] + tt.default_argv() + list(args)
        return subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_sys_exit_zero(self):
        """sys.exit(0) should exit with code 0."""
        rc = self._ipython_rc("-c", "import sys; sys.exit(0)")
        assert rc == 0

    def test_sys_exit_one(self):
        """sys.exit(1) should exit with code 1."""
        rc = self._ipython_rc("-c", "import sys; sys.exit(1)")
        assert rc == 1

    def test_sys_exit_two(self):
        """sys.exit(2) should exit with code 2, not 1."""
        rc = self._ipython_rc("-c", "import sys; sys.exit(2)")
        assert rc == 2

    def test_sys_exit_nonzero_arbitrary(self):
        """sys.exit(42) should exit with code 42."""
        rc = self._ipython_rc("-c", "import sys; sys.exit(42)")
        assert rc == 42

    def test_sys_exit_no_arg(self):
        """sys.exit() with no argument should exit with code 0."""
        rc = self._ipython_rc("-c", "import sys; sys.exit()")
        assert rc == 0

    def test_normal_execution_exits_zero(self):
        """Normal code should exit with code 0."""
        rc = self._ipython_rc("-c", "print('hello')")
        assert rc == 0

    def test_sys_exit_in_script(self):
        """sys.exit(2) in a script file should exit with code 2."""
        self.mktmp("import sys; sys.exit(2)\n")
        rc = self._ipython_rc("--", self.fname)
        assert rc == 2

    def test_sys_exit_zero_in_script(self):
        """sys.exit(0) in a script file should exit with code 0."""
        self.mktmp("import sys; sys.exit(0)\n")
        rc = self._ipython_rc("--", self.fname)
        assert rc == 0
