"""Tests for PDF export"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import logging
import os

from IPython.testing import decorators as dec

from .base import ExportersTestsBase
from ..pdf import PDFExporter


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestPDF(ExportersTestsBase):
    """Test PDF export"""

    exporter_class = PDFExporter

    def test_constructor(self):
        """Can a PDFExporter be constructed?"""
        self.exporter_class()


    @dec.onlyif_cmds_exist('pdflatex')
    @dec.onlyif_cmds_exist('pandoc')
    def test_export(self):
        """Smoke test PDFExporter"""
        (output, resources) = self.exporter_class(latex_count=1).from_filename(self._get_notebook())
        self.assertIsInstance(output, bytes)
        assert len(output) > 0

