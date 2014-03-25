"""
Module with tests for the emptycode preprocessor
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

# Imports
from IPython.nbformat import current as nbformat

from .base import PreprocessorTestsBase
from ..emptycode import EmptyCodePreprocessor

# Class
class TestCoalesceStreams(PreprocessorTestsBase):
    """Contains test functions for emptycode.py"""

    def test_remove_empty(self):
        """Are empty code cells removed?"""
        cells=[                                                 # Index
            nbformat.new_code_cell(input="a", prompt_number=1), # 0
            nbformat.new_code_cell(input="", prompt_number=2),  # This will be removed.
            nbformat.new_text_cell("markdown", source=""),      # 1
            nbformat.new_text_cell("markdown", source="b"),     # 2
        ]
        worksheets = [nbformat.new_worksheet(name="worksheet1", cells=cells)]

        nb = nbformat.new_notebook(name="notebook1", worksheets=worksheets)
        res = self.build_resources()
        preprocessor = EmptyCodePreprocessor(enabled=True)
        nb, res = preprocessor(nb, res)
        self.assertEqual(nb.worksheets[0].cells[0].input, u'a')
        self.assertEqual(nb.worksheets[0].cells[1].cell_type, u'markdown')
        self.assertEqual(nb.worksheets[0].cells[1].source, u'')
        self.assertEqual(nb.worksheets[0].cells[2].source, u'b')
