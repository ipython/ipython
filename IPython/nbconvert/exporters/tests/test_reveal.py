"""
Module with tests for reveal.py
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
from ..reveal import RevealExporter
from IPython.testing.decorators import onlyif_cmds_exist

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestRevealExporter(ExportersTestsBase):
    """Contains test functions for reveal.py"""

    def test_constructor(self):
        """
        Can a RevealExporter be constructed?
        """
        RevealExporter()


    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a RevealExporter export something?
        """
        (output, resources) = RevealExporter().from_filename(self._get_notebook())
        assert len(output) > 0
