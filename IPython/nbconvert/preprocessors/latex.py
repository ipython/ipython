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

# Third-party import, needed for Pygments latex definitions.
from pygments.formatters import LatexFormatter

# ipy imports
from .base import (Preprocessor)
from IPython.nbconvert import filters

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class LatexPreprocessor(Preprocessor):
    """
    Converter for latex destined documents.
    """

    def preprocess(self, nb, resources):
        """
        Preprocessing to apply on each notebook.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """
        # Generate Pygments definitions for Latex 
        resources["pygment_definitions"] = LatexFormatter().get_style_defs()
        return super(LatexPreprocessor, self).preprocess(nb, resources)


    def preprocess_cell(self, cell, resources, index):
        """
        Apply a transformation on each cell,
        
        Parameters
        ----------
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        index : int
            Modified index of the cell being processed (see base.py)
        """
        
        #If the cell is a markdown cell, preprocess the ampersands used to
        #remove the space between them and their contents.  Latex will complain
        #if spaces exist between the ampersands and the math content.  
        #See filters.latex.rm_math_space for more information.
        if hasattr(cell, "source") and cell.cell_type == "markdown":
            cell.source = filters.strip_math_space(cell.source)
        return cell, resources
