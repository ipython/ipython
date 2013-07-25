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


    def test_export_full(self):
        """
        Can a LatexExporter export using 'full' flavor?
        """
        (output, resources) = LatexExporter(flavor='full').from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_basic(self):
        """
        Can a LatexExporter export using 'basic' flavor?
        """
        (output, resources) = LatexExporter(flavor='basic').from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_reveal(self):
        """
        Can a LatexExporter export using 'reveal' flavor?
        """
        (output, resources) = LatexExporter(flavor='reveal').from_filename(self._get_notebook())
        assert len(output) > 0