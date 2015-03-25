"""
Module with tests for templateexporter.py
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

from IPython.config import Config

from .base import ExportersTestsBase
from .cheese import CheesePreprocessor
from ..templateexporter import TemplateExporter


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestExporter(ExportersTestsBase):
    """Contains test functions for exporter.py"""


    def test_constructor(self):
        """
        Can a TemplateExporter be constructed?
        """
        TemplateExporter()


    def test_export(self):
        """
        Can a TemplateExporter export something?
        """
        exporter = self._make_exporter()
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert len(output) > 0


    def test_extract_outputs(self):
        """
        If the ExtractOutputPreprocessor is enabled, are outputs extracted?
        """
        config = Config({'ExtractOutputPreprocessor': {'enabled': True}})
        exporter = self._make_exporter(config=config)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert isinstance(resources['outputs'], dict)
        assert len(resources['outputs']) > 0


    def test_preprocessor_class(self):
        """
        Can a preprocessor be added to the preprocessors list by class type?
        """
        config = Config({'Exporter': {'preprocessors': [CheesePreprocessor]}})
        exporter = self._make_exporter(config=config)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert resources['cheese'] == 'real'


    def test_preprocessor_instance(self):
        """
        Can a preprocessor be added to the preprocessors list by instance?
        """
        config = Config({'Exporter': {'preprocessors': [CheesePreprocessor()]}})
        exporter = self._make_exporter(config=config)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert resources['cheese'] == 'real'


    def test_preprocessor_dottedobjectname(self):
        """
        Can a preprocessor be added to the preprocessors list by dotted object name?
        """
        config = Config({'Exporter': {'preprocessors': ['IPython.nbconvert.exporters.tests.cheese.CheesePreprocessor']}})
        exporter = self._make_exporter(config=config)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert resources['cheese'] == 'real'


    def test_preprocessor_via_method(self):
        """
        Can a preprocessor be added via the Exporter convenience method?
        """
        exporter = self._make_exporter()
        exporter.register_preprocessor(CheesePreprocessor, enabled=True)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert resources['cheese'] == 'real'


    def _make_exporter(self, config=None):
        # Create the exporter instance, make sure to set a template name since
        # the base TemplateExporter doesn't have a template associated with it.
        exporter = TemplateExporter(config=config, template_file='python')
        return exporter        
