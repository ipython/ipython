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
from IPython.testing.decorators import onlyif_cmds_exist

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestLatexExporter(ExportersTestsBase):
    """Contains test functions for latex.py"""

    exporter_class = LatexExporter
    should_include_raw = ['latex']

    def test_constructor(self):
        """
        Can a LatexExporter be constructed?
        """
        LatexExporter()


    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a LatexExporter export something?
        """
        (output, resources) = LatexExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_book(self):
        """
        Can a LatexExporter export using 'report' template?
        """
        (output, resources) = LatexExporter(template_file='report').from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_basic(self):
        """
        Can a LatexExporter export using 'article' template?
        """
        (output, resources) = LatexExporter(template_file='article').from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_article(self):
        """
        Can a LatexExporter export using 'article' template?
        """
        (output, resources) = LatexExporter(template_file='article').from_filename(self._get_notebook())
        assert len(output) > 0