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

#TODO: Come after extract

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .activatable import ActivatableTransformer

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ConvertFiguresTransformer(ActivatableTransformer):
    """
    Converts all of the outputs in a notebook from one format to another.
    """


    def __init__(self, from_formats, to_format, **kw):
        """
        Public constructor
        
        Parameters
        ----------
        from_formats : list [of string]
            Formats that the converter can convert from
        to_format : string
            Format that the converter converts to
        config : Config
            Configuration file structure
        **kw : misc
            Additional arguments
        """
        super(ConvertFiguresTransformer, self).__init__(**kw)

        #TODO: Configurable, singular
        self._from_formats = from_formats
        self._to_format = to_format


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
