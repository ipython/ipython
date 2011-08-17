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
