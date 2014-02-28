"""Tests for SlidesExporter"""

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
from IPython.testing.decorators import onlyif_any_cmd_exists

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestSlidesExporter(ExportersTestsBase):
    """Tests for SlidesExporter"""

    exporter_class = SlidesExporter
    should_include_raw = ['html']

    def test_constructor(self):
        """
        Can a SlidesExporter be constructed?
        """
        SlidesExporter()


    @onlyif_any_cmd_exists('nodejs', 'node', 'pandoc')
    def test_export(self):
        """
        Can a SlidesExporter export something?
        """
        (output, resources) = SlidesExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_any_cmd_exists('nodejs', 'node', 'pandoc')
    def test_export_reveal(self):
        """
        Can a SlidesExporter export using the 'reveal' template?
        """
        (output, resources) = SlidesExporter(template_file='slides_reveal').from_filename(self._get_notebook())
        assert len(output) > 0
