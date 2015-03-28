"""Module that allows latex output notebooks to be conditioned before
they are converted.
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

from .base import Preprocessor

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class LatexPreprocessor(Preprocessor):
    """Preprocessor for latex destined documents.
    
    Mainly populates the `latex` key in the resources dict,
    adding definitions for pygments highlight styles.
    """

    def preprocess(self, nb, resources):
        """Preprocessing to apply on each notebook.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """
        # Generate Pygments definitions for Latex
        from pygments.formatters import LatexFormatter
        
        resources.setdefault("latex", {})
        resources["latex"].setdefault("pygments_definitions", LatexFormatter().get_style_defs())
        return nb, resources
