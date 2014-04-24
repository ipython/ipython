"""
Module with tests for the execute preprocessor.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import copy
import os
import re

from IPython.nbformat import current as nbformat

from .base import PreprocessorTestsBase
from ..execute import ExecutePreprocessor


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestExecute(PreprocessorTestsBase):
    """Contains test functions for execute.py"""

    @staticmethod
    def normalize_cell(cell):
        """
        Normalizes cells for comparison.
        """
        cell = dict(cell)
        if 'metadata' in cell:
            del cell['metadata']
        if 'text' in cell:
            cell['text'] = re.sub('0x[0-9a-f]{7,9}', '<HEXADDR>', cell['text'])
        if 'svg' in cell:
            del cell['text']
        return cell


    def assert_notebooks_equal(self, expected, actual):
        expected_cells = expected['worksheets'][0]['cells']
        actual_cells = actual['worksheets'][0]['cells']
        assert len(expected_cells) == len(actual_cells)

        for expected_cell, actual_cell in zip(expected_cells, actual_cells):
            expected_outputs = expected_cell.get('outputs', [])
            actual_outputs = actual_cell.get('outputs', [])
            normalized_expected_outputs = map(self.normalize_cell, expected_outputs)
            normalized_actual_outputs = map(self.normalize_cell, actual_outputs)
            assert normalized_expected_outputs == normalized_actual_outputs


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = ExecutePreprocessor()
        preprocessor.enabled = True
        return preprocessor


    def test_constructor(self):
        """Can a ExecutePreprocessor be constructed?"""
        self.build_preprocessor()


    def test_run_notebooks(self):
        """Runs a series of test notebooks and compares them to their actual output"""
        current_dir = os.path.dirname(__file__)
        input_files = os.listdir(os.path.join(current_dir, 'input'))
        for filename in input_files:
            if not filename.endswith(".ipynb"):
                continue
            with open(os.path.join(current_dir, 'input', filename)) as f:
                input_nb = nbformat.read(f, 'ipynb')
            with open(os.path.join(current_dir, 'expected', filename)) as f:
                expected_nb = nbformat.read(f, 'ipynb')
            res = self.build_resources()
            preprocessor = self.build_preprocessor()
            output_nb, _ = preprocessor(input_nb, res)
            self.assert_notebooks_equal(output_nb, expected_nb)

