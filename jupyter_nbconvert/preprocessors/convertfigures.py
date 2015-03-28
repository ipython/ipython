"""Module containing a preprocessor that converts outputs in the notebook from 
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

from .base import Preprocessor
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ConvertFiguresPreprocessor(Preprocessor):
    """
    Converts all of the outputs in a notebook from one format to another.
    """

    from_format = Unicode(config=True, help='Format the converter accepts')
    to_format = Unicode(config=True, help='Format the converter writes')

    def __init__(self, **kw):
        """
        Public constructor
        """
        super(ConvertFiguresPreprocessor, self).__init__(**kw)


    def convert_figure(self, data_format, data):
        raise NotImplementedError()


    def preprocess_cell(self, cell, resources, cell_index):
        """
        Apply a transformation on each cell,
        
        See base.py
        """

        # Loop through all of the datatypes of the outputs in the cell.
        for output in cell.get('outputs', []):
            if output.output_type in {'execute_result', 'display_data'} \
                    and self.from_format in output.data \
                    and self.to_format not in output.data:

                output.data[self.to_format] = self.convert_figure(
                            self.from_format, output.data[self.from_format])

        return cell, resources
