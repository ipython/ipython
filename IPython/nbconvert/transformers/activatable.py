"""
Contains base transformer with an enable/disable flag.
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

from .base import ConfigurableTransformer
from IPython.utils.traitlets import (Bool)

#-----------------------------------------------------------------------------
# Classes and Functions
#-----------------------------------------------------------------------------

class ActivatableTransformer(ConfigurableTransformer):
    """ConfigurableTransformer that has an enabled flag

    Inherit from this if you just want to have a transformer which is
    disable by default and can be enabled via the config by
        'c.YourTransformerName.enabled = True'
    """

    enabled = Bool(False, config=True)

    def __call__(self, nb, resources):
        """
        Transformation to apply on each notebook.
        
        You should return modified nb, resources.
        If you wish to apply your transform on each cell, you might want to 
        overwrite cell_transform method instead.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        """
        
        if not self.enabled :
            return nb, resources
        else :
            return super(ActivatableTransformer, self).__call__(nb, resources)
