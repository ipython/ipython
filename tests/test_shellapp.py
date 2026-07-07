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
import sys

import pytest

from IPython.terminal.ipapp import TerminalIPythonApp
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


# -----------------------------------------------------------------------------
# In-process tests for the InteractiveShellApp mixin
# -----------------------------------------------------------------------------


def test_init_path_inserts_before_site_packages(monkeypatch):
    """'' is added to sys.path just before the first site-packages entry."""
    app = TerminalIPythonApp()
    monkeypatch.setattr(
        sys, "path", ["/zzz/first", "/zzz/lib/python9.9/site-packages", "/zzz/last"]
    )
    app.init_path()
    assert sys.path.index("") == 1


def test_init_path_no_site_packages_inserts_front(monkeypatch):
    app = TerminalIPythonApp()
    monkeypatch.setattr(sys, "path", ["/zzz/first", "/zzz/last"])
    app.init_path()
    assert sys.path[0] == ""


def test_init_path_noop_when_already_present(monkeypatch):
    app = TerminalIPythonApp()
    monkeypatch.setattr(sys, "path", ["", "/zzz/first"])
    app.init_path()
    assert sys.path == ["", "/zzz/first"]


def test_init_path_ignore_cwd(monkeypatch):
    app = TerminalIPythonApp()
    app.ignore_cwd = True
    monkeypatch.setattr(sys, "path", ["/zzz/first"])
    app.init_path()
    assert "" not in sys.path


def test_user_ns_observer_syncs_shell():
    """Assigning app.user_ns rebinds the shell's user namespace."""
    from IPython.terminal.interactiveshell import TerminalInteractiveShell

    shell = TerminalInteractiveShell.instance()
    orig_ns = shell.user_ns
    app = TerminalIPythonApp()
    # with no shell attached, assigning user_ns is a no-op
    app.user_ns = {"zzz_ignored": 0}
    app.shell = shell
    custom = {"zzz_custom_ns_var": 1}
    try:
        app.user_ns = custom
        assert shell.user_ns is custom
        # init_user_ns() ran and injected the usual defaults
        assert "get_ipython" in custom
        assert custom["zzz_custom_ns_var"] == 1
    finally:
        shell.user_ns = orig_ns
        shell.init_user_ns()


def test_init_shell_not_implemented():
    from IPython.core.shellapp import InteractiveShellApp

    with pytest.raises(NotImplementedError):
        InteractiveShellApp().init_shell()
