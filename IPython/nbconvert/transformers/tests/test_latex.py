"""
Module with tests for the latex transformer
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
from ..latex import LatexTransformer


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestLatex(TransformerTestsBase):
    """Contains test functions for latex.py"""


    def build_transformer(self):
        """Make an instance of a transformer"""
        transformer = LatexTransformer()
        transformer.enabled = True
        return transformer

    def test_constructor(self):
        """Can a LatexTransformer be constructed?"""
        self.build_transformer()
        

    def test_output(self):
        """Test the output of the LatexTransformer"""
        nb, res = self.build_transformer()(self.build_notebook(), self.build_resources())

        # Make sure the code cell wasn't modified.
        self.assertEqual(nb.worksheets[0].cells[0].input, '$ e $')

        # Verify that the markdown cell was processed.
        self.assertEqual(nb.worksheets[0].cells[1].source, '$e$')
