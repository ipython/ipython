"""Tests for HTMLExporter"""

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
from ..html import HTMLExporter
from IPython.testing.decorators import onlyif_any_cmd_exists

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestHTMLExporter(ExportersTestsBase):
    """Tests for HTMLExporter"""
    
    exporter_class = HTMLExporter
    should_include_raw = ['html']

    def test_constructor(self):
        """
        Can a HTMLExporter be constructed?
        """
        HTMLExporter()


    @onlyif_any_cmd_exists('nodejs', 'node', 'pandoc')
    def test_export(self):
        """
        Can a HTMLExporter export something?
        """
        (output, resources) = HTMLExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_any_cmd_exists('nodejs', 'node', 'pandoc')
    def test_export_basic(self):
        """
        Can a HTMLExporter export using the 'basic' template?
        """
        (output, resources) = HTMLExporter(template_file='basic').from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_any_cmd_exists('nodejs', 'node', 'pandoc')
    def test_export_full(self):
        """
        Can a HTMLExporter export using the 'full' template?
        """
        (output, resources) = HTMLExporter(template_file='full').from_filename(self._get_notebook())
        assert len(output) > 0

