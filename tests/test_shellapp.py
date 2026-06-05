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
import pytest

from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils.io import temp_pyfile


@pytest.fixture
def tmp_pyfile():
    """Fixture that provides a mktmp helper and cleans up created files."""
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


def test_py_script_file_attribute(tmp_pyfile):
    """Test that `__file__` is set when running `ipython file.py`"""
    src = "print(__file__)\n"
    fname = tmp_pyfile(src)
    err = None
    tt.ipexec_validate(fname, fname, err)


def test_ipy_script_file_attribute(tmp_pyfile):
    """Test that `__file__` is set when running `ipython file.ipy`"""
    src = "print(__file__)\n"
    fname = tmp_pyfile(src, ext=".ipy")
    err = None
    tt.ipexec_validate(fname, fname, err)


# The commands option to ipexec_validate doesn't work on Windows, and it
# doesn't seem worth fixing
@dec.skip_win32
def test_py_script_file_attribute_interactively(tmp_pyfile):
    """Test that `__file__` is not set after `ipython -i file.py`"""
    src = "True\n"
    fname = tmp_pyfile(src)

    out, err = tt.ipexec(
        fname,
        options=["-i"],
        commands=['"__file__" in globals()', "print(123)", "exit()"],
    )
    assert "False" in out, f"Subprocess stderr:\n{err}\n-----"
