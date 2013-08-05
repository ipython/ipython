"""
Module with tests for the csshtmlheader transformer
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

from .base import TransformerTestsBase
from ..csshtmlheader import CSSHTMLHeaderTransformer


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestCSSHTMLHeader(TransformerTestsBase):
    """Contains test functions for csshtmlheader.py"""

    def test_constructor(self):
        """Can a CSSHTMLHeaderTransformer be constructed?"""
        CSSHTMLHeaderTransformer()
    

    def test_output(self):
        """Test the output of the CSSHTMLHeaderTransformer"""
        nb, res = CSSHTMLHeaderTransformer()(self.build_notebook(), {})
        assert 'inlining' in res
        assert 'css' in res['inlining'] 