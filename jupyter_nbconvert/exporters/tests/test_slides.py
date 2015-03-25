"""Tests for SlidesExporter"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import ExportersTestsBase
from ..slides import SlidesExporter


class TestSlidesExporter(ExportersTestsBase):
    """Tests for SlidesExporter"""

    exporter_class = SlidesExporter
    should_include_raw = ['html']

    def test_constructor(self):
        """
        Can a SlidesExporter be constructed?
        """
        SlidesExporter()


    def test_export(self):
        """
        Can a SlidesExporter export something?
        """
        (output, resources) = SlidesExporter().from_filename(self._get_notebook())
        assert len(output) > 0


    def test_export_reveal(self):
        """
        Can a SlidesExporter export using the 'reveal' template?
        """
        (output, resources) = SlidesExporter(template_file='slides_reveal').from_filename(self._get_notebook())
        assert len(output) > 0
