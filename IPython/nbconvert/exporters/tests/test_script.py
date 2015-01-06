"""Tests for ScriptExporter"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys

from IPython.nbformat import v4
from IPython.utils.py3compat import PY3

from .base import ExportersTestsBase
from ..script import ScriptExporter


class TestScriptExporter(ExportersTestsBase):
    """Tests for ScriptExporter"""

    exporter_class = ScriptExporter

    def test_constructor(self):
        """Construct ScriptExporter"""
        e = self.exporter_class()

    def test_export(self):
        """ScriptExporter can export something"""
        (output, resources) = self.exporter_class().from_filename(self._get_notebook())
        assert len(output) > 0
    
    def test_export_python(self):
        """delegate to custom exporter from language_info"""
        exporter = self.exporter_class()
        
        pynb = v4.new_notebook()
        (output, resources) = self.exporter_class().from_notebook_node(pynb)
        self.assertNotIn('# coding: utf-8', output)
        
        pynb.metadata.language_info = {
            'name': 'python',
            'mimetype': 'text/x-python',
            'nbconvert_exporter': 'python',
        }
        (output, resources) = self.exporter_class().from_notebook_node(pynb)
        self.assertIn('# coding: utf-8', output)

        