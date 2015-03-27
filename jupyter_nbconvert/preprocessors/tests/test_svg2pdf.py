"""Tests for the svg2pdf preprocessor"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.testing import decorators as dec
from IPython.nbformat import v4 as nbformat

from .base import PreprocessorTestsBase
from ..svg2pdf import SVG2PDFPreprocessor


class Testsvg2pdf(PreprocessorTestsBase):
    """Contains test functions for svg2pdf.py"""

    simple_svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->
<svg
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   version="1.0"
   x="0.00000000"
   y="0.00000000"
   width="500.00000"
   height="500.00000"
   id="svg2">
  <defs
     id="defs4" />
  <g
     id="layer1">
    <rect
       width="300.00000"
       height="300.00000"
       x="100.00000"
       y="100.00000"
       style="opacity:1.0000000;fill:none;fill-opacity:1.0000000;fill-rule:evenodd;stroke:#000000;stroke-width:8.0000000;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4.0000000;stroke-dasharray:none;stroke-dashoffset:0.00000000;stroke-opacity:1.0000000"
       id="rect5719" />
  </g>
</svg>"""

    def build_notebook(self):
        """Build a reveal slides notebook in memory for use with tests.
        Overrides base in PreprocessorTestsBase"""

        outputs = [nbformat.new_output(output_type='display_data',
                                       data={'image/svg+xml':self.simple_svg})
                  ]

        cells=[nbformat.new_code_cell(source="", execution_count=1, outputs=outputs)]

        return nbformat.new_notebook(cells=cells)


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = SVG2PDFPreprocessor()
        preprocessor.enabled = True
        return preprocessor


    def test_constructor(self):
        """Can a SVG2PDFPreprocessor be constructed?"""
        self.build_preprocessor()


    @dec.onlyif_cmds_exist('inkscape')
    def test_output(self):
        """Test the output of the SVG2PDFPreprocessor"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        self.assertIn('application/pdf', nb.cells[0].outputs[0].data)
