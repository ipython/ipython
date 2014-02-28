"""Module containing a preprocessor that extracts all of the outputs from the
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
from mimetypes import guess_extension

from IPython.utils.traitlets import Unicode, Set
from .base import Preprocessor
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ExtractOutputPreprocessor(Preprocessor):
    """
    Extracts all of the outputs from the notebook file.  The extracted 
    outputs are returned in the 'resources' dictionary.
    """

    output_filename_template = Unicode(
        "{unique_key}_{cell_index}_{index}{extension}", config=True)

    extract_output_types = Set({'png', 'jpeg', 'svg', 'application/pdf'}, config=True)

    def preprocess_cell(self, cell, resources, cell_index):
        """
        Apply a transformation on each cell,
        
        Parameters
        ----------
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        cell_index : int
            Index of the cell being processed (see base.py)
        """

        #Get the unique key from the resource dict if it exists.  If it does not 
        #exist, use 'output' as the default.  Also, get files directory if it
        #has been specified
        unique_key = resources.get('unique_key', 'output')
        output_files_dir = resources.get('output_files_dir', None)
        
        #Make sure outputs key exists
        if not isinstance(resources['outputs'], dict):
            resources['outputs'] = {}
            
        #Loop through all of the outputs in the cell
        for index, out in enumerate(cell.get('outputs', [])):

            #Get the output in data formats that the template needs extracted
            for out_type in self.extract_output_types:
                if out_type in out:
                    data = out[out_type]

                    #Binary files are base64-encoded, SVG is already XML
                    if out_type in {'png', 'jpeg', 'application/pdf'}:

                        # data is b64-encoded as text (str, unicode)
                        # decodestring only accepts bytes
                        data = py3compat.cast_bytes(data)
                        data = base64.decodestring(data)
                    elif sys.platform == 'win32':
                        data = data.replace('\n', '\r\n').encode("UTF-8")
                    else:
                        data = data.encode("UTF-8")
                    
                    # Build an output name
                    # filthy hack while we have some mimetype output, and some not
                    if '/' in out_type:
                        ext = guess_extension(out_type)
                        if ext is None:
                            ext = '.' + out_type.rsplit('/')[-1]
                    else:
                        ext = '.' + out_type
                    
                    filename = self.output_filename_template.format(
                                    unique_key=unique_key,
                                    cell_index=cell_index,
                                    index=index,
                                    extension=ext)

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
