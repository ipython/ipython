"""Module containing a transformer that extracts all of the figures from the
notebook file.  The extracted figures are returned in the 'resources' dictionary.
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

import sys
from IPython.utils.traitlets import Unicode
from .base import Transformer

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ExtractFigureTransformer(Transformer):
    """
    Extracts all of the figures from the notebook file.  The extracted 
    figures are returned in the 'resources' dictionary.
    """

    figure_filename_template = Unicode(
        "{unique_key}_{cell_index}_{index}.{extension}", config=True)


    def transform_cell(self, cell, resources, cell_index):
        """
        Apply a transformation on each cell,
        
        Parameters
        ----------
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        cell_index : int
            Index of the cell being processed (see base.py)
        """

        #Get the unique key from the resource dict if it exists.  If it does not 
        #exist, use 'figure' as the default.
        unique_key = resources.get('unique_key', 'figure')
        
        #Make sure figures key exists
        if not 'figures' in resources:
            resources['figures'] = {}
            
        #Loop through all of the outputs in the cell
        for index, out in enumerate(cell.get('outputs', [])):

            #Get the output in data formats that the template is interested in.
            for out_type in self.display_data_priority:
                if out.hasattr(out_type):
                    data = out[out_type]

                    #Binary files are base64-encoded, SVG is already XML
                    if out_type in ('png', 'jpg', 'jpeg', 'pdf'):
                        data = data.decode('base64')
                    elif sys.platform == 'win32':
                        data = data.replace('\n', '\r\n').encode("UTF-8")
                    else:
                        data = data.encode("UTF-8")
                    
                    #Build a figure name
                    figure_name = self.figure_filename_template.format( 
                                    unique_key=unique_key,
                                    cell_index=cell_index,
                                    index=index,
                                    extension=out_type)

                    #On the cell, make the figure available via 
                    #   cell.outputs[i].svg_filename  ... etc (svg in example)
                    # Where
                    #   cell.outputs[i].svg  contains the data
                    out[out_type + '_filename'] = figure_name

                    #In the resources, make the figure available via
                    #   resources['figures']['filename'] = data
                    resources['figures'][figure_name] = data

        return cell, resources
