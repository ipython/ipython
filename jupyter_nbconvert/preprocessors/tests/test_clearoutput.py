"""
Module with tests for the clearoutput preprocessor.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import PreprocessorTestsBase
from ..clearoutput import ClearOutputPreprocessor


class TestClearOutput(PreprocessorTestsBase):
    """Contains test functions for clearoutput.py"""


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = ClearOutputPreprocessor()
        preprocessor.enabled = True
        return preprocessor

    def test_constructor(self):
        """Can a ClearOutputPreprocessor be constructed?"""
        self.build_preprocessor()

    def test_output(self):
        """Test the output of the ClearOutputPreprocessor"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        assert nb.cells[0].outputs == []
        assert nb.cells[0].execution_count is None
