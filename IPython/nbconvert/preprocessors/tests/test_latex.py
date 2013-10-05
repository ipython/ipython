"""
Module with tests for the latex preprocessor
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

from .base import PreprocessorTestsBase
from ..latex import LatexPreprocessor


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestLatex(PreprocessorTestsBase):
    """Contains test functions for latex.py"""


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = LatexPreprocessor()
        preprocessor.enabled = True
        return preprocessor

    def test_constructor(self):
        """Can a LatexPreprocessor be constructed?"""
        self.build_preprocessor()
        

    def test_output(self):
        """Test the output of the LatexPreprocessor"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)

        # Make sure the code cell wasn't modified.
        self.assertEqual(nb.worksheets[0].cells[0].input, '$ e $')

        # Verify that the markdown cell wasn't processed.
        self.assertEqual(nb.worksheets[0].cells[1].source, '$ e $')
