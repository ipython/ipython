"""
Module with tests for the HighlightMagics preprocessor
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
from ..highlightmagics import HighlightMagicsPreprocessor


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestHighlightMagics(PreprocessorTestsBase):
    """Contains test functions for highlightmagics.py"""


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = HighlightMagicsPreprocessor()
        preprocessor.enabled = True
        return preprocessor

    def test_constructor(self):
        """Can a HighlightMagicsPreprocessor be constructed?"""
        self.build_preprocessor()

    def test_tagging(self):
        """Test the HighlightMagicsPreprocessor tagging"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb.worksheets[0].cells[0].input = """%%R -i x,y -o XYcoef
            lm.fit <- lm(y~x)
            par(mfrow=c(2,2))
            print(summary(lm.fit))
            plot(lm.fit)
            XYcoef <- coef(lm.fit)"""

        nb, res = preprocessor(nb, res)

        assert('magics_language' in nb.worksheets[0].cells[0]['metadata'])

        self.assertEqual(nb.worksheets[0].cells[0]['metadata']['magics_language'], 'r')

    def test_no_false_positive(self):
        """Test that HighlightMagicsPreprocessor does not tag false positives"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb.worksheets[0].cells[0].input = """# this should not be detected
                print(\"""
                %%R -i x, y
                \""")"""
        nb, res = preprocessor(nb, res)

        assert('magics_language' not in nb.worksheets[0].cells[0]['metadata'])