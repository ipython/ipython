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


    def build_transformer(self):
        """Make an instance of a transformer"""
        transformer = CSSHTMLHeaderTransformer()
        transformer.enabled = True
        return transformer


    def test_constructor(self):
        """Can a CSSHTMLHeaderTransformer be constructed?"""
        self.build_transformer()
    

    def test_output(self):
        """Test the output of the CSSHTMLHeaderTransformer"""
        nb = self.build_notebook()
        res = self.build_resources()
        transformer = self.build_transformer()
        nb, res = transformer(nb, res)
        assert 'inlining' in res
        assert 'css' in res['inlining'] 