#!/usr/bin/env python
"""
Contains writer for writing nbconvert output to filesystem.
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

import io
import os
import shutil
import glob

from IPython.utils.traitlets import Unicode

from .base import WriterBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class FileWriter(WriterBase):
    """Consumes nbconvert output and produces files."""


    build_directory = Unicode("nbconvert_build", config=True, 
                              help="""Directory to write output to.  Leave blank
                              to output to the current directory""")


    def __init__(self, config, **kw):
        """
        Constructor
        """
        super(FileWriter, self).__init__(config=config, **kw)
    

    def write(self, notebook_name, output_extension, output, resources):
            """
            Consume and write Jinja output to the file system.  Output directory
            is set via the 'build_directory' variable of this instance (a 
            configurable).

            Parameters
            ----------
            notebook_filename : string
                Name of the notebook file that was converted (no extension or 
                full path).
            output_extension : string
                Extension to give the output when written to the destination.
            output : string
                Conversion results.  This string contains the file contents of 
                the converted file.
            resources : dict
                Resources created and filled by the nbconvert conversion
                process.  Includes output from transformers, such as the extract 
                figure transformer.
            """

            #If the user specifies an output directory, use it.
            destination = None
            if len(self.build_directory) > 0:

                #Make sure that the output directory exists.
                if not os.path.isdir(self.build_directory):
                    os.mkdir(self.build_directory)
                destination = self.build_directory

            #Write all of the extracted resources to the destination directory.
            #NOTE: WE WRITE EVERYTHING AS-IF IT'S BINARY SINCE WE DON'T KNOW
            #IF IT'S TEXT OR BINARY.  AT THE TIME OF WRITING, THIS ONLY
            #AFFECTS SVG FILE LINE ENDINGS ON WINDOWS.  THE SVG FILES WILL STILL
            #WORK IN ANY READER, THEY JUST WONT BE AS HUMAN READABLE (A 
            #CONVERSION WILL BE REQUIRED).
            for (filename, data) in self._get_extracted_figures(resources).items():

                #Determine where to write the file to
                if not destination is None:
                    destination_filename = os.path.join(destination, filename)
                else:
                    destination_filename = filename

                #Write file
                with io.open(destination_filename, 'wb') as f:
                        f.write(data)

            #Copy referenced files to output directory
            if not destination is None:
                for filename in self.files:

                    #Copy files that match search pattern
                    for matching_filename in glob.glob(filename):
                        shutil.copyfile(matching_filename, 
                                        os.path.join(destination, filename))

            #Determine where to write conversion results.
            destination_filename = notebook_name + '.' + output_extension
            if not destination is None:
                destination_filename = os.path.join(destination, 
                                                    destination_filename)
                
            #Write conversion results.
            with io.open(destination_filename, 'w') as f:
                f.write(output)
