# encoding: utf-8
"""
Test the LineFrontEnd
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is
#  in the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

from IPython.frontend.linefrontendbase import LineFrontEndBase
from copy import deepcopy
import nose.tools as nt

class ConcreteLineFrontEnd(LineFrontEndBase):
    """ A concrete class to test the LineFrontEndBase.
    """
    def capture_output(self):
        pass

    def release_output(self):
        pass


def test_is_complete():
    """ Tests line completion heuristic.
    """
    frontend = ConcreteLineFrontEnd()
    yield nt.assert_true, not frontend.is_complete('for x in \\')
    yield nt.assert_true, not frontend.is_complete('for x in (1, ):')
    yield nt.assert_true, frontend.is_complete('for x in (1, ):\n  pass')


