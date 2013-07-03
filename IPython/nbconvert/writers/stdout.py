#!/usr/bin/env python
"""
Contains Stdout writer
"""
#-----------------------------------------------------------------------------
#Copyright (c) 2013, the IPython Development Team.
#
#Distributed under the terms of the Modified BSD License.
#
#The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .base import WriterBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class StdoutWriter(WriterBase):
    """Consumes output from nbconvert export...() methods and writes to the 
    stdout stream.  Allows for quick debuging of nbconvert output.  Using the
    debug flag makes the writer pretty-print the figures contained within the
    notebook."""


    def __init__(self, config=None, debug=False, **kw):
        """
        Constructor
        """
        super(StdoutWriter, self).__init__(config=config, **kw)
        self._debug = debug


    def write(self, notebook_name, output_extension, output, resources, 
              referenced_files=[]):
        """
        Consume and write Jinja output.

        Parameters
        ----------
        notebook_filename : string
            Name of the notebook file that was converted.
        output_extension : string
            Extension to give the output when written to the destination.
        output : string
            Conversion results.  This string contains the file contents of the
            converted file.
        resources : dict
            Resources created and filled by the nbconvert conversion process.
            Includes output from transformers, such as the extract figure 
            transformer.
        referenced_files : list [of string]
            List of the files that the notebook references.  Files will be 
            included with written output.
        """

        #If in debug mode, write resources instead of output.
        if self._debug:
            import pprint
            pprint.pprint(self._get_extracted_figures(resources), indent=4)
        else:
            print(output)
