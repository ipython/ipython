"""
Module with tests for the clearoutput preprocessor.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import copy

from IPython.nbformat import current as nbformat

from .base import PreprocessorTestsBase
from ..execute import ExecutePreprocessor


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestExecute(PreprocessorTestsBase):
    """Contains test functions for execute.py"""


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = ExecutePreprocessor()
        preprocessor.enabled = True
        return preprocessor

    def test_constructor(self):
        """Can a ExecutePreprocessor be constructed?"""
        self.build_preprocessor()

    def test_correct_output(self):
        """Test that ExecutePreprocessor evaluates a cell to the right thing"""
        nb = self.build_notebook()
        res = self.build_resources()
        nb.worksheets[0].cells[0].input = "print 'hi!'"
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        expected_outputs = [{'output_type': 'stream', 'stream': 'stdout', 'text': 'hi!\n'}] 
        assert nb.worksheets[0].cells[0].outputs == expected_outputs
