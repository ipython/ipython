"""Latex transformer.

Module that allows latex output notebooks to be conditioned before
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
from .transformers import (ActivatableTransformer) #TODO

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class LatexTransformer(ActivatableTransformer):
    """
    Converter for latex destined documents.
    """

    def cell_transform(self, cell, other, index):
        """
        Apply a transformation on each cell,

        receive the current cell, the resource dict and the index of current cell as parameter.

        Returns modified cell and resource dict.
        """
        
        if hasattr(cell, "source") and cell.cell_type == "markdown":
            cell.source = rm_math_space(cell.source)
        return cell, other
