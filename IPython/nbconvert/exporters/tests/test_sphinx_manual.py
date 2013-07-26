"""
Module with tests for sphinx_manual.py
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
from ..sphinx_manual import SphinxManualExporter
from IPython.testing.decorators import onlyif_cmds_exist

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestSphinxManualExporter(ExportersTestsBase):
    """Contains test functions for sphinx_manual.py"""

    def test_constructor(self):
        """
        Can a SphinxManualExporter be constructed?
        """
        SphinxManualExporter()


    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a SphinxManualExporter export something?
        """
        (output, resources) = SphinxManualExporter().from_filename(self._get_notebook())
        assert len(output) > 0
