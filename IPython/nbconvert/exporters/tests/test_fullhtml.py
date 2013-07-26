"""
Module with tests for fullhtml.py
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
from ..fullhtml import FullHTMLExporter
from IPython.testing.decorators import onlyif_cmds_exist

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestFullHTMLExporter(ExportersTestsBase):
    """Contains test functions for fullhtml.py"""

    def test_constructor(self):
        """
        Can a FullHTMLExporter be constructed?
        """
        FullHTMLExporter()

    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a FullHTMLExporter export something?
        """
        (output, resources) = FullHTMLExporter().from_filename(self._get_notebook())
        assert len(output) > 0
