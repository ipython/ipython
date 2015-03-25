"""
Module with tests for the serve post-processor
"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from ...tests.base import TestsBase
from ..serve import ServePostProcessor


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestServe(TestsBase):
    """Contains test functions for serve.py"""


    def test_constructor(self):
        """Can a ServePostProcessor be constructed?"""
        ServePostProcessor()
