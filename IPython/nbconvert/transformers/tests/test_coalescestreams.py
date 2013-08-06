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

from .base import TransformerTestsBase
from ..coalescestreams import coalesce_streams


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestCoalesceStreams(TransformerTestsBase):
    """Contains test functions for coalescestreams.py"""

    def test_coalesce_streams(self):
        """coalesce_streams transformer output test"""
        nb, res = coalesce_streams(self.build_notebook(), self.build_resources())
        outputs = nb.worksheets[0].cells[0].outputs
        self.assertEqual(outputs[0].text, "a")
        self.assertEqual(outputs[1].output_type, "text")
        self.assertEqual(outputs[2].text, "cd")
        self.assertEqual(outputs[3].text, "ef")
    