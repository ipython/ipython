"""
Module with tests for python.py
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
from ..python import PythonExporter

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestPythonExporter(ExportersTestsBase):
    """Contains test functions for python.py"""

    def test_constructor(self):
        """
        Can a PythonExporter be constructed?
        """
        PythonExporter()


    def test_export(self):
        """
        Can a PythonExporter export something?
        """
        (output, resources) = PythonExporter().from_filename(self._get_notebook())
        assert len(output) > 0