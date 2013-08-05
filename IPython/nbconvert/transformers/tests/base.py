"""
Module with utility functions for transformer tests
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

from IPython.nbformat import current as nbformat

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TransformerTestsBase(TestsBase):
    """Contains test functions transformer tests"""


    def build_notebook(self):
        """Build a notebook in memory for use with transformer tests"""

        outputs = [nbformat.new_output(output_type="stream", stream="stdout", output_text="a"),
                   nbformat.new_output(output_type="text", output_text="b"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="c"),
                   nbformat.new_output(output_type="stream", stream="stdout", output_text="d"),
                   nbformat.new_output(output_type="stream", stream="stderr", output_text="e"),
                   nbformat.new_output(output_type="stream", stream="stderr", output_text="f"),
                   nbformat.new_output(output_type="png", output_png='Zw==')] #g
        
        cells=[nbformat.new_code_cell(input="$ e $", prompt_number=1,outputs=outputs),
               nbformat.new_text_cell('markdown', source="$ e $")]
        worksheets = [nbformat.new_worksheet(name="worksheet1", cells=cells)]

        return nbformat.new_notebook(name="notebook1", worksheets=worksheets)
