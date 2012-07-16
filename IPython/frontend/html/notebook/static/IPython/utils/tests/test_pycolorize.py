"""Test suite for our color utilities.

Authors
-------

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# third party
import nose.tools as nt

# our own
from IPython.utils.PyColorize import Parser

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def test_unicode_colorize():
    p = Parser()
    f1 = p.format('1/0', 'str')
    f2 = p.format(u'1/0', 'str')
    nt.assert_equals(f1, f2)

