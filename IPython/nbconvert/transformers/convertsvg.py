"""Module containing a transformer that converts outputs in the notebook from 
one format to another.
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

from .convertoutputs import ConvertOutputsTransformer

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ConvertSvgTransformer(ConvertOutputsTransformer):
    """
    Converts all of the outputs in a notebook from one format to another.
    """


    def __init__(self, **kw):
        """
        Public constructor
        
        Parameters
        ----------
        config : Config
            Configuration file structure
        **kw : misc
            Additional arguments
        """
        super(ConvertSvgTransformer, self).__init__(['svg'], 'png', **kw)


    def convert_figure(self, data_format, data):
        #TODO
        raise NotImplementedError()
