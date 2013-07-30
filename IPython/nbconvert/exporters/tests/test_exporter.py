"""
Module with tests for exporter.py
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
from .cheese import CheeseTransformer
from ..exporter import Exporter


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestExporter(ExportersTestsBase):
    """Contains test functions for exporter.py"""


    def test_constructor(self):
        """
        Can an Exporter be constructed?
        """
        Exporter()


    def test_export(self):
        """
        Can an Exporter export something?
        """
        exporter = self._make_exporter()
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert len(output) > 0


    def test_extract_outputs(self):
        """
        If the ExtractOutputTransformer is enabled, are outputs extracted?
        """
        config = Config({'ExtractOutputTransformer': {'enabled': True}})
        exporter = self._make_exporter(config=config)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert 'outputs' in resources
        assert len(resources['outputs']) > 0


    def test_transformer_class(self):
        """
        Can a transformer be added to the transformers list by class type?
        """
        config = Config({'Exporter': {'transformers': [CheeseTransformer]}})
        exporter = self._make_exporter(config=config)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert 'cheese' in resources
        assert resources['cheese'] == 'real'


    def test_transformer_instance(self):
        """
        Can a transformer be added to the transformers list by instance?
        """
        config = Config({'Exporter': {'transformers': [CheeseTransformer()]}})
        exporter = self._make_exporter(config=config)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert 'cheese' in resources
        assert resources['cheese'] == 'real'


    def test_transformer_dottedobjectname(self):
        """
        Can a transformer be added to the transformers list by dotted object name?
        """
        config = Config({'Exporter': {'transformers': ['IPython.nbconvert.exporters.tests.cheese.CheeseTransformer']}})
        exporter = self._make_exporter(config=config)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert 'cheese' in resources
        assert resources['cheese'] == 'real'


    def test_transformer_via_method(self):
        """
        Can a transformer be added via the Exporter convenience method?
        """
        exporter = self._make_exporter()
        exporter.register_transformer(CheeseTransformer, enabled=True)
        (output, resources) = exporter.from_filename(self._get_notebook())
        assert resources is not None
        assert 'cheese' in resources
        assert resources['cheese'] == 'real'


    def _make_exporter(self, config=None):
        #Create the exporter instance, make sure to set a template name since
        #the base Exporter doesn't have a template associated with it.
        exporter = Exporter(config=config, template_file='python')
        return exporter        