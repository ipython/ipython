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
