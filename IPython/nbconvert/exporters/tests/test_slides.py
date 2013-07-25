"""
Module with tests for slides.py
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
from ..slides import SlidesExporter

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestSlidesExporter(ExportersTestsBase):
    """Contains test functions for slides.py"""

    def test_constructor(self):
        """
        Can a SlidesExporter be constructed?
        """
        SlidesExporter()


    def test_export(self):
        """
        Can a SlidesExporter export something?
        """
        (output, resources) = SlidesExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_reveal(self):
        """
        Can a SlidesExporter export using the 'reveal' flavor?
        """
        (output, resources) = SlidesExporter(flavor='reveal').from_filename(self._get_notebook())
        assert len(output) > 0
