# encoding: utf-8
"""
Tests for platutils.py
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys

import nose.tools as nt

from IPython.utils.platutils import find_cmd, FindCmdError, get_long_path_name
from IPython.testing import decorators as dec

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

def test_find_cmd_python():
    """Make sure we find sys.exectable for python."""
    nt.assert_equals(find_cmd('python'), sys.executable)

    
@dec.skip_win32
def test_find_cmd_ls():
    """Make sure we can find the full path to ls."""
    path = find_cmd('ls')
    nt.assert_true(path.endswith('ls'))

    
def has_pywin32():
    try:
        import win32api
    except ImportError:
        return False
    return True


@dec.onlyif(has_pywin32, "This test requires win32api to run")
def test_find_cmd_pythonw():
    """Try to find pythonw on Windows."""
    path = find_cmd('pythonw')
    nt.assert_true(path.endswith('pythonw.exe'))


@dec.onlyif(lambda : sys.platform != 'win32' or has_pywin32(),
            "This test runs on posix or in win32 with win32api installed")
def test_find_cmd_fail():
    """Make sure that FindCmdError is raised if we can't find the cmd."""
    nt.assert_raises(FindCmdError,find_cmd,'asdfasdf')

    
@dec.skip_if_not_win32
def test_get_long_path_name_win32():
    p = get_long_path_name('c:\\docume~1')
    nt.assert_equals(p,u'c:\\Documents and Settings') 

    
@dec.skip_win32
def test_get_long_path_name():
    p = get_long_path_name('/usr/local')
    nt.assert_equals(p,'/usr/local')
