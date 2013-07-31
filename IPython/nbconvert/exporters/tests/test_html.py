"""
Module with tests for html.py
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
from ..html import HTMLExporter
from IPython.testing.decorators import onlyif_cmds_exist

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestHTMLExporter(ExportersTestsBase):
    """Contains test functions for html.py"""

    def test_constructor(self):
        """
        Can a HTMLExporter be constructed?
        """
        HTMLExporter()


    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a HTMLExporter export something?
        """
        (output, resources) = HTMLExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_basic(self):
        """
        Can a HTMLExporter export using the 'basic' template?
        """
        (output, resources) = HTMLExporter(template_file='basic').from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_full(self):
        """
        Can a HTMLExporter export using the 'full' template?
        """
        (output, resources) = HTMLExporter(template_file='full').from_filename(self._get_notebook())
        assert len(output) > 0
