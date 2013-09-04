"""
Module with tests for the sphinx preprocessor
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

from .base import PreprocessorTestsBase
from ..sphinx import SphinxPreprocessor


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestSphinx(PreprocessorTestsBase):
    """Contains test functions for sphinx.py"""


    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = SphinxPreprocessor()
        preprocessor.enabled = True
        return preprocessor


    def test_constructor(self):
        """Can a SphinxPreprocessor be constructed?"""
        self.build_preprocessor()
    

    def test_resources(self):
        """Make sure the SphinxPreprocessor adds the appropriate resources to the
        resources dict."""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        assert "texinputs" in res['sphinx']
