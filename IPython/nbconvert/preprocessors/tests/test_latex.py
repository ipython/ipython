"""Tests for the latex preprocessor"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import PreprocessorTestsBase
from ..latex import LatexPreprocessor


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
        self.assertEqual(nb.cells[0].source, '$ e $')

        # Verify that the markdown cell wasn't processed.
        self.assertEqual(nb.cells[1].source, '$ e $')
