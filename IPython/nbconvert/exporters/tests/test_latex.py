"""
Module with tests for latex.py
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
from ..latex import LatexExporter

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestLatexExporter(ExportersTestsBase):
    """Contains test functions for latex.py"""

    def test_constructor(self):
        """
        Can a LatexExporter be constructed?
        """
        LatexExporter()


    def test_export(self):
        """
        Can a LatexExporter export something?
        """
        (output, resources) = LatexExporter().from_filename(self._get_notebook())
        assert len(output) > 0