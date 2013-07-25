"""
Module with tests for basichtml.py
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
from ..basichtml import BasicHTMLExporter
from IPython.testing.decorators import onlyif_cmds_exist

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestBasicHTMLExporter(ExportersTestsBase):
    """Contains test functions for basichtml.py"""

    def test_constructor(self):
        """
        Can a BasicHTMLExporter be constructed?
        """
        BasicHTMLExporter()

    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a BasicHTMLExporter export something?
        """
        (output, resources) = BasicHTMLExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_basic(self):
        """
        Can a BasicHTMLExporter export using the 'basic' flavor?
        """
        (output, resources) = BasicHTMLExporter(flavor='basic').from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_full(self):
        """
        Can a BasicHTMLExporter export using the 'full' flavor?
        """
        (output, resources) = BasicHTMLExporter(flavor='full').from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_reveal(self):
        """
        Can a BasicHTMLExporter export using the 'reveal' flavor?
        """
        (output, resources) = BasicHTMLExporter(flavor='reveal').from_filename(self._get_notebook())
        assert len(output) > 0