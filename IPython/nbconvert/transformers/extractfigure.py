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
BINARY_KEY = "binary"
TEXT_KEY = "text"

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
    
    key_format_map =  Dict({}, config=True,)
    figure_name_format_map =  Dict({}, config=True)

    #TODO: Change this to .format {} syntax
    default_key_template = Unicode('_fig_{index:02d}.{ext}', config=True)

    def __init__(self, config=None, **kw):
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

        # A unique index for association with extracted figures
        self.index_generator = itertools.count(1)

    def cell_transform(self, cell, resources, index):
        """
        Apply a transformation on each cell,
        
        Parameters
        ----------
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        index : int
            Index of the cell being processed (see base.py)
        """
        
        if resources.get(FIGURES_KEY, None) is None :
            resources[FIGURES_KEY] = {TEXT_KEY:{},BINARY_KEY:{}}
            
        for out in cell.get('outputs', []):
            for out_type in self.display_data_priority:
                
                if out.hasattr(out_type):
                    figname, key, data, binary = self._new_figure(out[out_type], out_type)
                    out['key_'+out_type] = figname
                    
                    if binary :
                        resources[FIGURES_KEY][BINARY_KEY][key] = data
                    else :
                        resources[FIGURES_KEY][TEXT_KEY][key] = data
                        
                    index += 1
        return cell, resources


    def _get_override_extension(self, extension):
        """Gets the overriden extension if it exists, else returns extension. 

        Parameters
        ----------
        extension : str
            File extension.
        """
        
        if extension in self.extra_extension_map :
            return self.extra_extension_map[extension]
    
        return extension


    def _new_figure(self, data, format):
        """Create a new figure file in the given format.

        Parameters
        ----------
        data : str
            Cell data (from Notebook node cell)
        format : str
            Figure format
        index : int
            Index of the figure being extracted
        """
        
        figure_name_template = self.figure_name_format_map.get(format, self.default_key_template)
        key_template = self.key_format_map.get(format, self.default_key_template)
        
        #TODO: option to pass the hash as data?
        index = next(self.index_generator)
        figure_name = figure_name_template.format(index=index, ext=self._get_override_extension(format))
        key = key_template.format(index=index, ext=self._get_override_extension(format))

        #Binary files are base64-encoded, SVG is already XML
        binary = False
        if format in ('png', 'jpg', 'pdf'):
            data = data.decode('base64')
            binary = True

        return figure_name, key, data, binary
