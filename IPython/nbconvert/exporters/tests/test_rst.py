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
from ..rst import RstExporter

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class Test_RstExporter(ExportersTestsBase):
    """Contains test functions for rst.py"""

    def test_constructor(self):
        """
        Can a RstExporter be constructed?
        """
        RstExporter()


    def test_export(self):
        """
        Can a RstExporter export something?
        """
        (output, resources) = RstExporter().from_filename(self._get_notebook())
        assert len(output) > 0