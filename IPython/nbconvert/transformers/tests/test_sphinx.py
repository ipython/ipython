"""
Module with tests for the sphinx transformer
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

from .base import TransformerTestsBase
from ..sphinx import SphinxTransformer


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestSphinx(TransformerTestsBase):
    """Contains test functions for sphinx.py"""


    def build_transformer(self):
        """Make an instance of a transformer"""
        transformer = SphinxTransformer()
        transformer.enabled = True
        return transformer


    def test_constructor(self):
        """Can a SphinxTransformer be constructed?"""
        self.build_transformer()
    

    def test_resources(self):
        """Make sure the SphinxTransformer adds the appropriate resources to the
        resources dict."""
        nb = self.build_notebook()
        res = self.build_resources()
        transformer = self.build_transformer()
        nb, res = transformer(nb, res)
        assert 'sphinx' in res
        assert "author" in res['sphinx']
        assert "version" in res['sphinx']
        assert "release" in res['sphinx']
        assert "date" in res['sphinx']
        assert "chapterstyle" in res['sphinx']
        assert "outputstyle" in res['sphinx']
        assert "centeroutput" in res['sphinx']
        assert "header" in res['sphinx']
        assert "texinputs" in res['sphinx']
        assert "pygment_definitions" in res['sphinx']
