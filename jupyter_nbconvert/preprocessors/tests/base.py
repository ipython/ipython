"""utility functions for preprocessor tests"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.nbformat import v4 as nbformat

from ...tests.base import TestsBase
from ...exporters.exporter import ResourcesDict


class PreprocessorTestsBase(TestsBase):
    """Contains test functions preprocessor tests"""


    def build_notebook(self):
        """Build a notebook in memory for use with preprocessor tests"""

        outputs = [
            nbformat.new_output("stream", name="stdout", text="a"),
            nbformat.new_output("display_data", data={'text/plain': 'b'}),
            nbformat.new_output("stream", name="stdout", text="c"),
            nbformat.new_output("stream", name="stdout", text="d"),
            nbformat.new_output("stream", name="stderr", text="e"),
            nbformat.new_output("stream", name="stderr", text="f"),
            nbformat.new_output("display_data", data={'image/png': 'Zw=='}), # g
            nbformat.new_output("display_data", data={'application/pdf': 'aA=='}), # h
        ]
        
        cells=[nbformat.new_code_cell(source="$ e $", execution_count=1, outputs=outputs),
               nbformat.new_markdown_cell(source="$ e $")]

        return nbformat.new_notebook(cells=cells)


    def build_resources(self):
        """Build an empty resources dictionary."""
        
        res = ResourcesDict()
        res['metadata'] = ResourcesDict()
        return res
