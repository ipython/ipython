"""
Module with tests for the execute preprocessor.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import copy
import glob
import io
import os
import re

from IPython import nbformat

from .base import PreprocessorTestsBase
from ..execute import ExecutePreprocessor

from IPython.nbconvert.filters import strip_ansi

addr_pat = re.compile(r'0x[0-9a-f]{7,9}')

class TestExecute(PreprocessorTestsBase):
    """Contains test functions for execute.py"""

    @staticmethod
    def normalize_output(output):
        """
        Normalizes outputs for comparison.
        """
        output = dict(output)
        if 'metadata' in output:
            del output['metadata']
        if 'text' in output:
            output['text'] = re.sub(addr_pat, '<HEXADDR>', output['text'])
        if 'text/plain' in output.get('data', {}):
            output['data']['text/plain'] = \
                re.sub(addr_pat, '<HEXADDR>', output['data']['text/plain'])
        if 'traceback' in output:
            tb = []
            for line in output['traceback']:
                tb.append(strip_ansi(line))
            output['traceback'] = tb
            
        return output


    def assert_notebooks_equal(self, expected, actual):
        expected_cells = expected['cells']
        actual_cells = actual['cells']
        self.assertEqual(len(expected_cells), len(actual_cells))

        for expected_cell, actual_cell in zip(expected_cells, actual_cells):
            expected_outputs = expected_cell.get('outputs', [])
            actual_outputs = actual_cell.get('outputs', [])
            normalized_expected_outputs = list(map(self.normalize_output, expected_outputs))
            normalized_actual_outputs = list(map(self.normalize_output, actual_outputs))
            self.assertEqual(normalized_expected_outputs, normalized_actual_outputs)

            expected_execution_count = expected_cell.get('execution_count', None)
            actual_execution_count = actual_cell.get('execution_count', None)
            self.assertEqual(expected_execution_count, actual_execution_count)


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
        input_files = glob.glob(os.path.join(current_dir, 'files', '*.ipynb'))
        for filename in input_files:
            with io.open(os.path.join(current_dir, 'files', filename)) as f:
                input_nb = nbformat.read(f, 4)
            res = self.build_resources()
            preprocessor = self.build_preprocessor()
            cleaned_input_nb = copy.deepcopy(input_nb)
            for cell in cleaned_input_nb.cells:
                if 'execution_count' in cell:
                    del cell['execution_count']
                cell['outputs'] = []
            output_nb, _ = preprocessor(cleaned_input_nb, res)
            self.assert_notebooks_equal(output_nb, input_nb)
