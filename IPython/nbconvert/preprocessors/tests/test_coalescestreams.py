"""
Module with tests for the coalescestreams preprocessor
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
from IPython.nbformat import current as nbformat

from .base import PreprocessorTestsBase
from ..coalescestreams import coalesce_streams


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------
class TestCoalesceStreams(PreprocessorTestsBase):
    """Contains test functions for coalescestreams.py"""

    def test_coalesce_streams(self):
        """coalesce_streams preprocessor output test"""
        nb = self.build_notebook()
        res = self.build_resources()
        nb, res = coalesce_streams(nb, res)
        outputs = nb.worksheets[0].cells[0].outputs
        self.assertEqual(outputs[0].text, "a")
        self.assertEqual(outputs[1].output_type, "text")
        self.assertEqual(outputs[2].text, "cd")
        self.assertEqual(outputs[3].text, "ef")

    def test_coalesce_sequenced_streams(self):
        """Can the coalesce streams preprocessor merge a sequence of streams?"""
        outputs = [nbformat.new_output(output_type="stream", stream="stdout", output_text="0"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="1"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="2"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="3"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="4"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="5"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="6"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="7")]
        cells=[nbformat.new_code_cell(input="# None", prompt_number=1,outputs=outputs)]
        worksheets = [nbformat.new_worksheet(name="worksheet1", cells=cells)]

        nb = nbformat.new_notebook(name="notebook1", worksheets=worksheets)
        res = self.build_resources()
        nb, res = coalesce_streams(nb, res)
        outputs = nb.worksheets[0].cells[0].outputs
        self.assertEqual(outputs[0].text, u'01234567')

    def test_coalesce_replace_streams(self):
        """Are \\r characters handled?"""
        outputs = [nbformat.new_output(output_type="stream", stream="stdout", output_text="z"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="\ra"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="\nz\rb"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="\nz"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="\rc\n"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="z\rz\rd")]
        cells=[nbformat.new_code_cell(input="# None", prompt_number=1,outputs=outputs)]
        worksheets = [nbformat.new_worksheet(name="worksheet1", cells=cells)]

        nb = nbformat.new_notebook(name="notebook1", worksheets=worksheets)
        res = self.build_resources()
        nb, res = coalesce_streams(nb, res)
        outputs = nb.worksheets[0].cells[0].outputs
        self.assertEqual(outputs[0].text, u'a\nb\nc\nd')
