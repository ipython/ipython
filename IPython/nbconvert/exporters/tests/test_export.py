"""
Module with tests for export.py
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

import os

from IPython.nbformat import current as nbformat

from .base import ExportersTestsBase
from ..export import *
from ..python import PythonExporter

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestExport(ExportersTestsBase):
    """Contains test functions for export.py"""


    def test_export_wrong_name(self):
        """
        Is the right error thrown when a bad template name is used?
        """
        try:
            export_by_name('not_a_name', self._get_notebook())
        except ExporterNameError as e:
            pass


    def test_export_filename(self):
        """
        Can a notebook be exported by filename?
        """
        (output, resources) = export_by_name('python', self._get_notebook())
        assert len(output) > 0


    def test_export_nbnode(self):
        """
        Can a notebook be exported by a notebook node handle?
        """
        with open(self._get_notebook(), 'r') as f:
            notebook = nbformat.read(f, 'json')
            (output, resources) = export_by_name('python', notebook)
        assert len(output) > 0


    def test_export_filestream(self):
        """
        Can a notebook be exported by a filesteam?
        """
        with open(self._get_notebook(), 'r') as f:
            (output, resources) = export_by_name('python', f)
        assert len(output) > 0


    def test_export_using_exporter(self):
        """
        Can a notebook be exported using an instanciated exporter?
        """
        (output, resources) = export(PythonExporter(), self._get_notebook())
        assert len(output) > 0


    def test_export_using_exporter_class(self):
        """
        Can a notebook be exported using an exporter class type?
        """
        (output, resources) = export(PythonExporter, self._get_notebook())
        assert len(output) > 0


    def test_export_resources(self):
        """
        Can a notebook be exported along with a custom resources dict?
        """
        (output, resources) = export(PythonExporter, self._get_notebook(), resources={})
        assert len(output) > 0


    def test_no_exporter(self):
        """
        Is the right error thrown if no exporter is provided?
        """
        try:
            (output, resources) = export(None, self._get_notebook())
        except TypeError:
            pass
                