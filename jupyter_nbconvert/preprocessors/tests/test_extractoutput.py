"""Tests for the extractoutput preprocessor"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import PreprocessorTestsBase
from ..extractoutput import ExtractOutputPreprocessor


class TestExtractOutput(PreprocessorTestsBase):
    """Contains test functions for extractoutput.py"""

    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = ExtractOutputPreprocessor()
        preprocessor.extract_output_types = {'text/plain', 'image/png', 'application/pdf'}
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
        output = nb.cells[0].outputs[1]
        self.assertIn('filenames', output.metadata)
        self.assertIn('text/plain', output.metadata.filenames)
        text_filename = output.metadata.filenames['text/plain']

        # Check if png was extracted.
        output = nb.cells[0].outputs[6]
        self.assertIn('filenames', output.metadata)
        self.assertIn('image/png', output.metadata.filenames)
        png_filename = output.metadata.filenames['image/png']
        
        # Check that pdf was extracted
        output = nb.cells[0].outputs[7]
        self.assertIn('filenames', output.metadata)
        self.assertIn('application/pdf', output.metadata.filenames)
        pdf_filename = output.metadata.filenames['application/pdf']

        # Verify text output
        self.assertIn(text_filename, res['outputs'])
        self.assertEqual(res['outputs'][text_filename], b'b')

        # Verify png output
        self.assertIn(png_filename, res['outputs'])
        self.assertEqual(res['outputs'][png_filename], b'g')

        # Verify pdf output
        self.assertIn(pdf_filename, res['outputs'])
        self.assertEqual(res['outputs'][pdf_filename], b'h')
