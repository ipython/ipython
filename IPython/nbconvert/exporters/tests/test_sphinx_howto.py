"""
Module with tests for sphinx_howto.py
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
from ..sphinx_howto import SphinxHowtoExporter
from IPython.testing.decorators import onlyif_cmds_exist

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestSphinxHowtoExporter(ExportersTestsBase):
    """Contains test functions for sphinx_howto.py"""

    def test_constructor(self):
        """
        Can a SphinxHowtoExporter be constructed?
        """
        SphinxHowtoExporter()


    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a SphinxHowtoExporter export something?
        """
        (output, resources) = SphinxHowtoExporter().from_filename(self._get_notebook())
        assert len(output) > 0
