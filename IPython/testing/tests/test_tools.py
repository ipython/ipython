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
from IPython.testing.tools import full_path, parse_test_output

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


def test_parser():
    err = ("FAILED (errors=1)", 1, 0)
    fail = ("FAILED (failures=1)", 0, 1)
    both = ("FAILED (errors=1, failures=1)", 1, 1)
    for txt, nerr, nfail in [err, fail, both]:
        nerr1, nfail1 = parse_test_output(txt)
        yield (nt.assert_equal, nerr, nerr1)
        yield (nt.assert_equal, nfail, nfail1)
