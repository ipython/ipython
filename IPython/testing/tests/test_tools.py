#!/usr/bin/env python
# encoding: utf-8
"""
Tests for testing.tools
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

from IPython.testing import decorators as dec
from IPython.testing.tools import full_path

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


@dec.skip_win32
def test_full_path_posix():
    spath = '/foo/bar.py'
    result = full_path(spath,['a.txt','b.txt'])
    nt.assert_equal(result, ['/foo/a.txt', '/foo/b.txt'])
    spath = '/foo'
    result = full_path(spath,['a.txt','b.txt'])
    nt.assert_equal(result, ['/a.txt', '/b.txt'])
    result = full_path(spath,'a.txt')
    nt.assert_equal(result, ['/a.txt'])


@dec.skip_if_not_win32
def test_full_path_win32():
    spath = 'c:\\foo\\bar.py'
    result = full_path(spath,['a.txt','b.txt'])
    nt.assert_equal(result, ['c:\\foo\\a.txt', 'c:\\foo\\b.txt'])
    spath = 'c:\\foo'
    result = full_path(spath,['a.txt','b.txt'])
    nt.assert_equal(result, ['c:\\a.txt', 'c:\\b.txt'])
    result = full_path(spath,'a.txt')
    nt.assert_equal(result, ['c:\\a.txt'])