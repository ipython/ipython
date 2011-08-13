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
    """Test columnize with very long inputs"""
    text.columnize(['a'*180, 'b'*180])
