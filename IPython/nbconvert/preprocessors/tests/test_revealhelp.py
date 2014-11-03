"""Tests for the revealhelp preprocessor"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.nbformat import v4 as nbformat

from .base import PreprocessorTestsBase
from ..revealhelp import RevealHelpPreprocessor


class Testrevealhelp(PreprocessorTestsBase):
    """Contains test functions for revealhelp.py"""

    def build_notebook(self):
        """Build a reveal slides notebook in memory for use with tests.
        Overrides base in PreprocessorTestsBase"""

        outputs = [nbformat.new_output(output_type="stream", name="stdout", text="a")]

        slide_metadata = {'slideshow' : {'slide_type': 'slide'}}
        subslide_metadata = {'slideshow' : {'slide_type': 'subslide'}}

        cells=[nbformat.new_code_cell(source="", execution_count=1, outputs=outputs),
               nbformat.new_markdown_cell(source="", metadata=slide_metadata),
               nbformat.new_code_cell(source="", execution_count=2, outputs=outputs),
               nbformat.new_markdown_cell(source="", metadata=slide_metadata),
               nbformat.new_markdown_cell(source="", metadata=subslide_metadata)]

        return nbformat.new_notebook(cells=cells)


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = RevealHelpPreprocessor()
        preprocessor.enabled = True
        return preprocessor


    def test_constructor(self):
        """Can a RevealHelpPreprocessor be constructed?"""
        self.build_preprocessor()


    def test_reveal_attribute(self):
        """Make sure the reveal url_prefix resources is set"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        assert 'reveal' in res
        assert  'url_prefix' in res['reveal']


    def test_reveal_output(self):
        """Make sure that the reveal preprocessor """
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        cells = nb.cells
        
        # Make sure correct metadata tags are available on every cell.
        for cell in cells:
            assert 'slide_type' in cell.metadata

        # Make sure slide end is only applied to the cells preceeding slide 
        # cells.
        assert 'slide_helper' in cells[1].metadata
        self.assertEqual(cells[1].metadata['slide_helper'], '-')

        # Verify 'slide-end'
        assert 'slide_helper' in cells[0].metadata
        self.assertEqual(cells[0].metadata['slide_helper'], 'slide_end')
        assert 'slide_helper' in cells[2].metadata
        self.assertEqual(cells[2].metadata['slide_helper'], 'slide_end')
        assert 'slide_helper' in cells[3].metadata
        self.assertEqual(cells[3].metadata['slide_helper'], 'subslide_end')
