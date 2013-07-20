"""
Contains CheeseTransformer
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

from ...transformers.base import Transformer

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class CheeseTransformer(Transformer):
    """
    Adds a cheese tag to the resources object
    """


    def __init__(self, **kw):
        """
        Public constructor
        """
        super(CheeseTransformer, self).__init__(**kw)


    def call(self, nb, resources):
        """
        Sphinx transformation to apply on each notebook.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        """
        resources['cheese'] = 'real'
        return nb, resources
