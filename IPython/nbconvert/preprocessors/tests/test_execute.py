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

    def prepare_cell(self, cell):
        cell = dict(cell)
        if 'metadata' in cell:
            del cell['metadata']
        if 'text' in cell:
            cell['text'] = re.sub('0x[0-9a-f]{7,9}', '<HEXADDR>', cell['text'])
        return cell


    def assert_notebooks_equal(self, expected, actual):
        expected_cells = expected['worksheets'][0]['cells']
        actual_cells = actual['worksheets'][0]['cells']
        assert len(expected_cells) == len(actual_cells)

        # TODO: what does this code do?
        for expected_out, actual_out in zip(expected_cells, actual_cells):
            for k in set(expected_out).union(actual_out):
                if k == 'outputs':
                    self.assertEquals(len(expected_out[k]), len(actual_out[k]))
                    for e, a in zip(expected_out[k], actual_out[k]):
                        assert self.prepare_cell(e) == self.prepare_cell(a)


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

