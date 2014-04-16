"""Module containing a preprocessor that removes the outputs from code cells"""

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

from .base import Preprocessor


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ClearOutputPreprocessor(Preprocessor):
    """
    Removes the output from all code cells in a notebook.
    """

    def preprocess_cell(self, cell, resources, cell_index):
        """
        Apply a transformation on each cell. See base.py for details.
        """
        if cell.cell_type == 'code':
            cell.outputs = []
        return cell, resources
