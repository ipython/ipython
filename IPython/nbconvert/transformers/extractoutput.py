"""Module containing a transformer that extracts all of the outputs from the
notebook file.  The extracted outputs are returned in the 'resources' dictionary.
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

import base64
import sys
import os

from IPython.utils.traitlets import Unicode
from .base import Transformer
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ExtractOutputTransformer(Transformer):
    """
    Extracts all of the outputs from the notebook file.  The extracted 
    outputs are returned in the 'resources' dictionary.
    """

    output_filename_template = Unicode(
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
        #exist, use 'output' as the default.  Also, get files directory if it
        #has been specified
        unique_key = resources.get('unique_key', 'output')
        output_files_dir = resources.get('output_files_dir', None)
        
        #Make sure outputs key exists
        if not 'outputs' in resources:
            resources['outputs'] = {}
            
        #Loop through all of the outputs in the cell
        for index, out in enumerate(cell.get('outputs', [])):

            #Get the output in data formats that the template is interested in.
            for out_type in self.display_data_priority:
                if out.hasattr(out_type):
                    data = out[out_type]

                    #Binary files are base64-encoded, SVG is already XML
                    if out_type in ('png', 'jpg', 'jpeg', 'pdf'):
                        # data is b64-encoded as text (str, unicode)
                        # decodestring only accepts bytes
                        data = py3compat.cast_bytes(data)
                        data = base64.decodestring(data)
                    elif sys.platform == 'win32':
                        data = data.replace('\n', '\r\n').encode("UTF-8")
                    else:
                        data = data.encode("UTF-8")
                    
                    #Build an output name
                    filename = self.output_filename_template.format( 
                                    unique_key=unique_key,
                                    cell_index=cell_index,
                                    index=index,
                                    extension=out_type)

                    #On the cell, make the figure available via 
                    #   cell.outputs[i].svg_filename  ... etc (svg in example)
                    # Where
                    #   cell.outputs[i].svg  contains the data
                    if output_files_dir is not None:
                        filename = os.path.join(output_files_dir, filename)
                    out[out_type + '_filename'] = filename

                    #In the resources, make the figure available via
                    #   resources['outputs']['filename'] = data
                    resources['outputs'][filename] = data

        return cell, resources
