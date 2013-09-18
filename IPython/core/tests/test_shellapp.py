# -*- coding: utf-8 -*-
"""Tests for shellapp module.

Authors
-------
* Bradley Froehle
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import unittest

from IPython.testing import decorators as dec
from IPython.testing import tools as tt

class TestFileToRun(unittest.TestCase, tt.TempFileMixin):
    """Test the behavior of the file_to_run parameter."""

    def test_py_script_file_attribute(self):
        """Test that `__file__` is set when running `ipython file.py`"""
        src = "print(__file__)\n"
        self.mktmp(src)

        if dec.module_not_available('sqlite3'):
            err = 'WARNING: IPython History requires SQLite, your history will not be saved\n'
        else:
            err = None
        tt.ipexec_validate(self.fname, self.fname, err)

    def test_ipy_script_file_attribute(self):
        """Test that `__file__` is set when running `ipython file.ipy`"""
        src = "print(__file__)\n"
        self.mktmp(src, ext='.ipy')

        if dec.module_not_available('sqlite3'):
            err = 'WARNING: IPython History requires SQLite, your history will not be saved\n'
        else:
            err = None
        tt.ipexec_validate(self.fname, self.fname, err)

    # Ideally we would also test that `__file__` is not set in the
    # interactive namespace after running `ipython -i <file>`.
