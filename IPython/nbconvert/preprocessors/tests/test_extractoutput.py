"""
Module with tests for the extractoutput preprocessor
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
from ..extractoutput import ExtractOutputPreprocessor


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestExtractOutput(PreprocessorTestsBase):
    """Contains test functions for extractoutput.py"""


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = ExtractOutputPreprocessor()
        preprocessor.enabled = True
        return preprocessor


    def test_constructor(self):
        """Can a ExtractOutputPreprocessor be constructed?"""
        self.build_preprocessor()
    

    def test_output(self):
        """Test the output of the ExtractOutputPreprocessor"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)

        # Check if text was extracted.
        output = nb.worksheets[0].cells[0].outputs[1]
        assert 'text_filename' in output
        text_filename = output['text_filename']

        # Check if png was extracted.
        output = nb.worksheets[0].cells[0].outputs[6]
        assert 'png_filename' in output
        png_filename = output['png_filename']

        # Verify text output
        assert text_filename in res['outputs']
        self.assertEqual(res['outputs'][text_filename], b'b')

        # Verify png output
        assert png_filename in res['outputs']
        self.assertEqual(res['outputs'][png_filename], b'g')
