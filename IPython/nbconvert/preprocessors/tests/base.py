"""utility functions for preprocessor tests"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.nbformat import current as nbformat

from ...tests.base import TestsBase
from ...exporters.exporter import ResourcesDict


class PreprocessorTestsBase(TestsBase):
    """Contains test functions preprocessor tests"""


    def build_notebook(self):
        """Build a notebook in memory for use with preprocessor tests"""

        outputs = [nbformat.new_output(output_type="stream", name="stdout", text="a"),
                   nbformat.new_output(output_type="display_data", mime_bundle={'text/plain': 'b'}),
                   nbformat.new_output(output_type="stream", name="stdout", text="c"),
                   nbformat.new_output(output_type="stream", name="stdout", text="d"),
                   nbformat.new_output(output_type="stream", name="stderr", text="e"),
                   nbformat.new_output(output_type="stream", name="stderr", text="f"),
                   nbformat.new_output(output_type="display_data", mime_bundle={'image/png': 'Zw=='})] # g
        out = nbformat.new_output(output_type="display_data")
        out['application/pdf'] = 'aA=='
        outputs.append(out)
        
        cells=[nbformat.new_code_cell(source="$ e $", prompt_number=1, outputs=outputs),
               nbformat.new_markdown_cell(source="$ e $")]

        return nbformat.new_notebook(cells=cells)


    def build_resources(self):
        """Build an empty resources dictionary."""
        
        res = ResourcesDict()
        res['metadata'] = ResourcesDict()
        return res
