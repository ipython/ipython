"""
Module with tests for markdown.py
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

from .base import ExportersTestsBase
from ..markdown import MarkdownExporter

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestMarkdownExporter(ExportersTestsBase):
    """Contains test functions for markdown.py"""

    def test_constructor(self):
        """
        Can a MarkdownExporter be constructed?
        """
        MarkdownExporter()


    def test_export(self):
        """
        Can a MarkdownExporter export something?
        """
        (output, resources) = MarkdownExporter().from_filename(self._get_notebook())
        assert len(output) > 0