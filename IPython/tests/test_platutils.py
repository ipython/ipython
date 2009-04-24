#!/usr/bin/env python
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

from IPython.platutils import find_cmd, FindCmdError
from IPython.testing import decorators as dec

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

def test_find_cmd_python():
    """Make sure we find sys.exectable for python."""
    nt.assert_equals(find_cmd('python'), sys.executable)

@dec.skip_win32
def test_find_cmd():
    """Make sure we can find the full path to ls."""
    path = find_cmd('ls')
    nt.assert_true(path.endswith('ls'))

@dec.skip_if_not_win32
def test_find_cmd():
    """Try to find pythonw on Windows."""
    path = find_cmd('pythonw')
    nt.assert_true(path.endswith('pythonw.exe'))

def test_find_cmd_fail():
    """Make sure that FindCmdError is raised if we can't find the cmd."""
    nt.assert_raises(FindCmdError,find_cmd,'asdfasdf')
