"""Tests for notebook.py"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import ExportersTestsBase
from ..notebook import NotebookExporter

class TestNotebookExporter(ExportersTestsBase):
    """Contains test functions for notebook.py"""

    exporter_class = NotebookExporter

    def test_export(self):
        """
        Does the NotebookExporter return the file unchanged?
        """
        with open(self._get_notebook()) as f:
            file_contents = f.read()
        (output, resources) = NotebookExporter().from_filename(self._get_notebook())
        assert len(output) > 0
        assert output == file_contents
