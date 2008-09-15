# encoding: utf-8
"""
Test the basic functionality of frontendbase. 
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is
#  in the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

from IPython.frontend.frontendbase import FrontEndBase

def test_iscomplete():
    """ Check that is_complete works. 
    """
    f = FrontEndBase()
    assert f.is_complete('(a + a)')
    assert not f.is_complete('(a + a')
    assert f.is_complete('1')
    assert not f.is_complete('1 + ')
    assert not f.is_complete('1 + \n\n')
    assert f.is_complete('if True:\n  print 1\n')
    assert not f.is_complete('if True:\n  print 1')
    assert f.is_complete('def f():\n  print 1\n')

if __name__ == '__main__':
    test_iscomplete()

