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
import itertools

from IPython.utils.traitlets import Dict, Unicode
from .activatable import ActivatableTransformer

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

FIGURES_KEY = "figures"

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ExtractFigureTransformer(ActivatableTransformer):
    """
    Extracts all of the figures from the notebook file.  The extracted 
    figures are returned in the 'resources' dictionary.
    """

    extra_extension_map =  Dict({},
        config=True,
        help="""Extra map to override extension based on type.
        Useful for latex where SVG will be converted to PDF before inclusion
        """)
    
    figure_filename_template = Unicode(
        "{notebook_name}_{cell_index}_{index}.{extension}", config=True)

    def __init__(self, notebook_name, config=None, **kw):
        """
        Public constructor
        
        Parameters
        ----------
        config : Config
            Configuration file structure
        **kw : misc
            Additional arguments
        """

        super(ExtractFigureTransformer, self).__init__(config=config, **kw)

        #A name unique to the notebook is needed to name files in build directly 
        #such that they do not conflict with other outputs from other notebooks
        #when the user is batch converting.  Unfortunately this needs to be here
        #so the template can be aware of what filename we are using.
        self._notebook_name = notebook_name

    def cell_transform(self, cell, resources, cell_index):
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
        
        #Make sure figures key exists@br
        if not FIGURES_KEY in resources:
            resources[FIGURES_KEY] = {}
            
        #A unique index for association with each output in the cell
        index_generator = itertools.count(0)

        #Loop through all of the outputs in the cell
        for out in cell.get('outputs', []):
            index = index_generator.next()

            #Get the output in data formats that the template is interested in.
            for out_type in self.display_data_priority:
                if out.hasattr(out_type):
                    data = out[out_type]

                    #Binary files are base64-encoded, SVG is already XML
                    if format in ('png', 'jpg', 'pdf'):
                        data = data.decode('base64')

                    #If the extension for the data type is different is 
                    #different than the name of the data type, change it here.
                    extension = out_type
                    if extension in self.extra_extension_map :
                        extension = self.extra_extension_map[extension]

                    #Build a figure name
                    figure_name = self.figure_filename_template.format( 
                                    notebook_name=self._notebook_name,
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
                    resources[FIGURES_KEY][figure_name] = data

        return cell, resources
