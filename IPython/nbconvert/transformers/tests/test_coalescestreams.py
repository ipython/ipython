"""
Module with tests for the coalescestreams transformer
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

from ...tests.base import TestsBase
from ..coalescestreams import coalesce_streams

from IPython.nbformat import current as nbformat

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestCoalesceStreams(TestsBase):
    """Contains test functions for coalescestreams.py"""


    def build_test_notebook(self):
        outputs = [nbformat.new_output(output_type="stream", stream="stdout", output_text="a"),
                   nbformat.new_output(output_type="text", output_text="b"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="c"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="d"),
                   nbformat.new_output(output_type="stream", stream="stderr", output_text="e"),
                   nbformat.new_output(output_type="stream", stream="stderr", output_text="f")]
        cells=[nbformat.new_code_cell(input="test",
            prompt_number=1,outputs=outputs)]
        worksheets = [nbformat.new_worksheet(name="worksheet1", cells=cells)]
        return nbformat.new_notebook(name="notebook1", worksheets=worksheets)

    def test_coalesce_streams(self):
        nb, res = coalesce_streams(self.build_test_notebook(), {})
        self.assertEqual(nb.worksheets[0].cells[0].outputs[0].text, "a")
        self.assertEqual(nb.worksheets[0].cells[0].outputs[1].output_type, "text")
        self.assertEqual(nb.worksheets[0].cells[0].outputs[2].text, "cd")
        self.assertEqual(nb.worksheets[0].cells[0].outputs[3].text, "ef")
    