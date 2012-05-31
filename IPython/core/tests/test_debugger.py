"""Tests for debugging machinery.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012, The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# third-party
import nose.tools as nt

# Our own
from IPython.core import debugger

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

def test_longer_repr():
    from repr import repr as trepr
    
    a = '1234567890'* 7
    ar = "'1234567890123456789012345678901234567890123456789012345678901234567890'"
    a_trunc = "'123456789012...8901234567890'"
    nt.assert_equals(trepr(a), a_trunc)
    # The creation of our tracer modifies the repr module's repr function
    # in-place, since that global is used directly by the stdlib's pdb module.
    t = debugger.Tracer()
    nt.assert_equals(trepr(a), ar)
