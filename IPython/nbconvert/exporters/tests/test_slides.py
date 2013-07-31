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
from IPython.testing.decorators import onlyif_cmds_exist

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


    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a SlidesExporter export something?
        """
        (output, resources) = SlidesExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_reveal(self):
        """
        Can a SlidesExporter export using the 'reveal' template?
        """
        (output, resources) = SlidesExporter(template_file='reveal').from_filename(self._get_notebook())
        assert len(output) > 0
