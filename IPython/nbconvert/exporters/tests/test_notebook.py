"""
Module with tests for notebook.py
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
from ..notebook import NotebookExporter

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestNotebookExporter(ExportersTestsBase):
    """Contains test functions for notebook.py"""

    exporter_class = NotebookExporter

    def test_constructor(self):
        """
        Can a NotebookExporter be constructed?
        """
        NotebookExporter()


    def test_export(self):
        """
        Does the NotebookExporter return the file unchanged?
        """
        with open(self._get_notebook()) as f:
            file_contents = f.read()
        (output, resources) = NotebookExporter().from_filename(self._get_notebook())
        assert len(output) > 0
        assert output == file_contents

