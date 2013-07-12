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

from .base import ConfigurableTransformer
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ConvertFiguresTransformer(ConfigurableTransformer):
    """
    Converts all of the outputs in a notebook from one format to another.
    """

    from_format = Unicode(config=True, help='Format the converter accepts')
    to_format = Unicode(config=True, help='Format the converter writes')

    def __init__(self, **kw):
        """
        Public constructor
        """
        super(ConvertFiguresTransformer, self).__init__(**kw)


    def convert_figure(self, data_format, data):
        raise NotImplementedError()


    def transform_cell(self, cell, resources, cell_index):
        """
        Apply a transformation on each cell,
        
        See base.py
        """

        #Loop through all of the datatypes of the outputs in the cell.
        for index, cell_out in enumerate(cell.get('outputs', [])):
            for data_type, data in cell_out.items():
                self._convert_figure(cell_out, data_type, data)
        return cell, resources


    def _convert_figure(self, cell_out, data_type, data):
        """
        Convert a figure and output the results to the cell output
        """

        if not self._to_format in cell_out:
            if data_type in self._from_formats:
                cell_out[self._to_format] = self.convert_figure(data_type, data)
