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

# Our own imports
# Needed to override transformer
from .activatable import (ActivatableTransformer)
from nbconvert.filters import latex

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class LatexTransformer(ActivatableTransformer):
    """
    Converter for latex destined documents.
    """

    def cell_transform(self, cell, resources, index):
        """
        Apply a transformation on each cell,
        
        Parameters
        ----------
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        index : int
            Modified index of the cell being processed (see base.py)
        """
        
        #If the cell is a markdown cell, preprocess the ampersands used to
        #remove the space between them and their contents.  Latex will complain
        #if spaces exist between the ampersands and the math content.  
        #See filters.latex.rm_math_space for more information.
        if hasattr(cell, "source") and cell.cell_type == "markdown":
            cell.source = latex.rm_math_space(cell.source)
        return cell, resources
