"""Module that allows custom Sphinx parameters to be set on the notebook and
on the 'other' object passed into Jinja.  Called prior to Jinja conversion
process.
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

from __future__ import print_function, absolute_import
import os
import sphinx
from .base import Preprocessor

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class SphinxPreprocessor(Preprocessor):
    """
    Sphinx utility preprocessor.

    This preprocessor is used to set variables needed by the latex to build
    Sphinx stylized templates.
    """
    
    def preprocess(self, nb, resources):
        """
        Sphinx preprocessing to apply on each notebook.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """
        
        # Find and pass in the path to the Sphinx dependencies.
        resources["sphinx"] = {}
        resources["sphinx"]["texinputs"] = os.path.realpath(os.path.join(sphinx.package_dir, "texinputs"))
        return nb, resources 
