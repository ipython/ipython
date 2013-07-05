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

from IPython.utils.traitlets import Dict, Unicode
from .activatable import ActivatableTransformer

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ExtractFigureTransformer(ActivatableTransformer):
    """
    Extracts all of the figures from the notebook file.  The extracted 
    figures are returned in the 'resources' dictionary.
    """


    figure_filename_template = Unicode(
        "{notebook_name}_{cell_index}_{index}.{extension}", config=True)


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
        super(ExtractFigureTransformer, self).__init__(**kw)


    def transform_cell(self, notebook_name, cell, resources, cell_index):
        """
        Apply a transformation on each cell,
        
        Parameters
        ----------
        notebook_name : string
            Name of the notebook
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        cell_index : int
            Index of the cell being processed (see base.py)
        """

        # #Make sure a notebook name is set.
        # if self.notebook_name is None:
        #     raise TypeError("_notebook_name")
        
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
                    if out_type in ('png', 'jpg', 'pdf'):
                        data = data.decode('base64')
                    else:
                        data = data.replace('\n', '\r\n')
                    
                    #Build a figure name
                    figure_name = self.figure_filename_template.format( 
                                    notebook_name=notebook_name,
                                    cell_index=cell_index,
                                    index=index,
                                    extension=extension)

                    #On the cell, make the figure available via 
                    #   cell.outputs[i].svg_filename  ... etc (svg in example)
                    # Where
                    #   cell.outputs[i].svg  contains the data
                    out[extension + '_filename'] = figure_name

                    #In the resources, make the figure available via
                    #   resources['figures']['filename'] = data
                    resources['figures'][figure_name] = data

        return cell, resources
