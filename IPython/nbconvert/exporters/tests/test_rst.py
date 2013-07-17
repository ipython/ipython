"""
Module with tests for rst.py
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
from ..rst import RSTExporter

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestRSTExporter(ExportersTestsBase):
    """Contains test functions for rst.py"""

    def test_constructor(self):
        """
        Can a RSTExporter be constructed?
        """
        RSTExporter()


    def test_export(self):
        """
        Can a RSTExporter export something?
        """
        (output, resources) = RSTExporter().from_filename(self._get_notebook())
        assert len(output) > 0