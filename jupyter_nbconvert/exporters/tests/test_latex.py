"""Tests for Latex exporter"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os.path
import textwrap
import re

from .base import ExportersTestsBase
from ..latex import LatexExporter
from IPython.nbformat import write
from IPython.nbformat import v4
from IPython.testing.decorators import onlyif_cmds_exist
from IPython.utils.tempdir import TemporaryDirectory


class TestLatexExporter(ExportersTestsBase):
    """Contains test functions for latex.py"""

    exporter_class = LatexExporter
    should_include_raw = ['latex']

    def test_constructor(self):
        """
        Can a LatexExporter be constructed?
        """
        LatexExporter()


    @onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a LatexExporter export something?
        """
        (output, resources) = LatexExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_book(self):
        """
        Can a LatexExporter export using 'report' template?
        """
        (output, resources) = LatexExporter(template_file='report').from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_basic(self):
        """
        Can a LatexExporter export using 'article' template?
        """
        (output, resources) = LatexExporter(template_file='article').from_filename(self._get_notebook())
        assert len(output) > 0


    @onlyif_cmds_exist('pandoc')
    def test_export_article(self):
        """
        Can a LatexExporter export using 'article' template?
        """
        (output, resources) = LatexExporter(template_file='article').from_filename(self._get_notebook())
        assert len(output) > 0

    @onlyif_cmds_exist('pandoc')
    def test_very_long_cells(self):
        """
        Torture test that long cells do not cause issues
        """
        lorem_ipsum_text = textwrap.dedent("""\
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec
          dignissim, ipsum non facilisis tempus, dui felis tincidunt metus,
          nec pulvinar neque odio eget risus. Nulla nisi lectus, cursus
          suscipit interdum at, ultrices sit amet orci. Mauris facilisis
          imperdiet elit, vitae scelerisque ipsum dignissim non. Integer
          consequat malesuada neque sit amet pulvinar. Curabitur pretium
          ut turpis eget aliquet. Maecenas sagittis lacus sed lectus
          volutpat, eu adipiscing purus pulvinar. Maecenas consequat
          luctus urna, eget cursus quam mollis a. Aliquam vitae ornare
          erat, non hendrerit urna. Sed eu diam nec massa egestas pharetra
          at nec tellus. Fusce feugiat lacus quis urna sollicitudin volutpat.
          Quisque at sapien non nibh feugiat tempus ac ultricies purus.
           """)
        lorem_ipsum_text = lorem_ipsum_text.replace("\n"," ") + "\n\n"
        large_lorem_ipsum_text = "".join([lorem_ipsum_text]*3000)

        notebook_name = "lorem_ipsum_long.ipynb"
        nb = v4.new_notebook(
            cells=[
                    v4.new_markdown_cell(source=large_lorem_ipsum_text)
            ]
        )

        with TemporaryDirectory() as td:
            nbfile = os.path.join(td, notebook_name)
            with open(nbfile, 'w') as f:
                write(nb, f, 4)

            (output, resources) = LatexExporter(template_file='article').from_filename(nbfile)
            assert len(output) > 0

    @onlyif_cmds_exist('pandoc')
    def test_prompt_number_color(self):
        """
        Does LatexExporter properly format input and output prompts in color?
        """
        (output, resources) = LatexExporter().from_filename(
            self._get_notebook(nb_name="prompt_numbers.ipynb"))
        in_regex = r"In \[\{\\color\{incolor\}(.*)\}\]:"
        out_regex = r"Out\[\{\\color\{outcolor\}(.*)\}\]:"

        ins = ["2", "10", " ", " ", "*", "0"]
        outs = ["10"]

        assert re.findall(in_regex, output) == ins
        assert re.findall(out_regex, output) == outs
