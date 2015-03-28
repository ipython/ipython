"""Tests for HTMLExporter"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import ExportersTestsBase
from ..html import HTMLExporter
from IPython.nbformat import v4
import re


class TestHTMLExporter(ExportersTestsBase):
    """Tests for HTMLExporter"""
    
    exporter_class = HTMLExporter
    should_include_raw = ['html']

    def test_constructor(self):
        """
        Can a HTMLExporter be constructed?
        """
        HTMLExporter()


    def test_export(self):
        """
        Can a HTMLExporter export something?
        """
        (output, resources) = HTMLExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_basic(self):
        """
        Can a HTMLExporter export using the 'basic' template?
        """
        (output, resources) = HTMLExporter(template_file='basic').from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_full(self):
        """
        Can a HTMLExporter export using the 'full' template?
        """
        (output, resources) = HTMLExporter(template_file='full').from_filename(self._get_notebook())
        assert len(output) > 0

    def test_prompt_number(self):
        """
        Does HTMLExporter properly format input and output prompts?
        """
        (output, resources) = HTMLExporter(template_file='full').from_filename(
            self._get_notebook(nb_name="prompt_numbers.ipynb"))
        in_regex = r"In&nbsp;\[(.*)\]:"
        out_regex = r"Out\[(.*)\]:"

        ins = ["2", "10", "&nbsp;", "&nbsp;", "*", "0"]
        outs = ["10"]

        assert re.findall(in_regex, output) == ins
        assert re.findall(out_regex, output) == outs

    def test_png_metadata(self):
        """
        Does HTMLExporter with the 'basic' template treat pngs with width/height metadata correctly?
        """
        (output, resources) = HTMLExporter(template_file='basic').from_filename(
            self._get_notebook(nb_name="pngmetadata.ipynb"))
        assert len(output) > 0

    def test_javascript_output(self):
        nb = v4.new_notebook(
            cells=[
                v4.new_code_cell(
                    outputs=[v4.new_output(
                        output_type='display_data',
                        data={
                            'application/javascript': "javascript_output();"
                        }
                    )]
                )
            ]
        )
        (output, resources) = HTMLExporter(template_file='basic').from_notebook_node(nb)
        self.assertIn('javascript_output', output)
