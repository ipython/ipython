"""
Module with tests for the extractoutput transformer
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
from ..extractoutput import ExtractOutputTransformer


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestExtractOutput(TransformerTestsBase):
    """Contains test functions for extractoutput.py"""


    def build_transformer(self):
        """Make an instance of a transformer"""
        transformer = ExtractOutputTransformer()
        transformer.enabled = True
        return transformer


    def test_constructor(self):
        """Can a ExtractOutputTransformer be constructed?"""
        self.build_transformer()
    

    def test_output(self):
        """Test the output of the ExtractOutputTransformer"""
        nb = self.build_notebook()
        res = self.build_resources()
        transformer = self.build_transformer()
        nb, res = transformer(nb, res)

        # Check if text was extracted.
        assert 'text_filename' in nb.worksheets[0].cells[0].outputs[1]
        text_filename = nb.worksheets[0].cells[0].outputs[1]['text_filename']

        # Check if png was extracted.
        assert 'png_filename' in nb.worksheets[0].cells[0].outputs[6]
        png_filename = nb.worksheets[0].cells[0].outputs[6]['png_filename']

        # Make sure an entry to the resources was added.
        assert 'outputs' in res

        # Verify text output
        assert text_filename in res['outputs']
        self.assertEqual(res['outputs'][text_filename], b'b')

        # Verify png output
        assert png_filename in res['outputs']
        self.assertEqual(res['outputs'][png_filename], b'g')
