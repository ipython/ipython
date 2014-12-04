"""Tests for RSTExporter"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import io

from IPython import nbformat
from IPython.nbformat import v4

from .base import ExportersTestsBase
from ..rst import RSTExporter
from IPython.testing.decorators import onlyif_cmds_exist


class TestRSTExporter(ExportersTestsBase):
    """Tests for RSTExporter"""

    exporter_class = RSTExporter
    should_include_raw = ['rst']

    def test_constructor(self):
        """
        Can a RSTExporter be constructed?
        """
        RSTExporter()


    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a RSTExporter export something?
        """
        (output, resources) = RSTExporter().from_filename(self._get_notebook())
        assert len(output) > 0
        
    @onlyif_cmds_exist('pandoc')
    def test_empty_code_cell(self):
        """No empty code cells in rst"""
        nbname = self._get_notebook()
        with io.open(nbname, encoding='utf8') as f:
            nb = nbformat.read(f, 4)
        
        exporter = self.exporter_class()
        
        (output, resources) = exporter.from_notebook_node(nb)
        # add an empty code cell
        nb.cells.append(
            v4.new_code_cell(source="")
        )
        (output2, resources) = exporter.from_notebook_node(nb)
        # adding an empty code cell shouldn't change output
        self.assertEqual(output.strip(), output2.strip())
        
