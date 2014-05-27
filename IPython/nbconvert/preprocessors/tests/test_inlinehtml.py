"""
Module with tests for the InlineHTML preprocessor
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import PreprocessorTestsBase
from ..inlinehtml import InlineHTMLPreprocessor


class TestInlineHTML(PreprocessorTestsBase):
    """Contains test functions for inlinehtml.py"""

    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = InlineHTMLPreprocessor()
        preprocessor.enabled = True
        return preprocessor

    def test_constructor(self):
        """Can a InlineHTMLPreprocessor be constructed?"""
        self.build_preprocessor()
    
    def test_output(self):
        """Test the output of the InlineHTMLPreprocessor"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        assert 'css' in res['inlining'] 
