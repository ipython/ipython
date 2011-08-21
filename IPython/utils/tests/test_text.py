# encoding: utf-8
"""Tests for IPython.utils.text"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import math

import nose.tools as nt

from nose import with_setup

from IPython.testing import decorators as dec
from IPython.utils import text

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

def test_columnize():
    """Basic columnize tests."""
    size = 5
    items = [l*size for l in 'abc']
    out = text.columnize(items, displaywidth=80)
    nt.assert_equals(out, 'aaaaa  bbbbb  ccccc\n')
    out = text.columnize(items, displaywidth=10)
    nt.assert_equals(out, 'aaaaa  ccccc\nbbbbb\n')


def test_columnize_long():
    """Test columnize with inputs longer than the display window"""
    text.columnize(['a'*81, 'b'*81], displaywidth=80)
    size = 11
    items = [l*size for l in 'abc']
    out = text.columnize(items, displaywidth=size-1)
    nt.assert_equals(out, '\n'.join(items+['']))

def test_eval_formatter():
    f = text.EvalFormatter()
    ns = dict(n=12, pi=math.pi, stuff='hello there', os=os)
    s = f.format("{n} {n/4} {stuff.split()[0]}", **ns)
    nt.assert_equals(s, "12 3 hello")
    s = f.format(' '.join(['{n//%i}'%i for i in range(1,8)]), **ns)
    nt.assert_equals(s, "12 6 4 3 2 2 1")
    s = f.format('{[n//i for i in range(1,8)]}', **ns)
    nt.assert_equals(s, "[12, 6, 4, 3, 2, 2, 1]")
    s = f.format("{stuff!s}", **ns)
    nt.assert_equals(s, ns['stuff'])
    s = f.format("{stuff!r}", **ns)
    nt.assert_equals(s, repr(ns['stuff']))
    
    nt.assert_raises(NameError, f.format, '{dne}', **ns)


def test_eval_formatter_slicing():
    f = text.EvalFormatter()
    f.allow_slicing = True
    ns = dict(n=12, pi=math.pi, stuff='hello there', os=os)
    s = f.format(" {stuff.split()[:]} ", **ns)
    nt.assert_equals(s, " ['hello', 'there'] ")
    s = f.format(" {stuff.split()[::-1]} ", **ns)
    nt.assert_equals(s, " ['there', 'hello'] ")
    s = f.format("{stuff[::2]}", **ns)
    nt.assert_equals(s, ns['stuff'][::2])
    
    nt.assert_raises(SyntaxError, f.format, "{n:x}", **ns)
    

def test_eval_formatter_no_slicing():
    f = text.EvalFormatter()
    f.allow_slicing = False
    ns = dict(n=12, pi=math.pi, stuff='hello there', os=os)
    
    s = f.format('{n:x} {pi**2:+f}', **ns)
    nt.assert_equals(s, "c +9.869604")
    
    nt.assert_raises(SyntaxError, f.format, "{a[:]}")

