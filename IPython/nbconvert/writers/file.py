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


    #Make sure that the output directory exists.
    def _build_directory_changed(self, name, old, new):
        if not os.path.isdir(new):
            os.mkdir(new) #TODO: makedirs


    def __init__(self, **kw):
        super(FileWriter, self).__init__(**kw)
        self._build_directory_changed('build_directory', self.build_directory, 
                                      self.build_directory)


    def write(self, notebook_name, output_extension, output, resources):
            """
            Consume and write Jinja output to the file system.  Output directory
            is set via the 'build_directory' variable of this instance (a 
            configurable).

            See base for more...
            """

            #Write all of the extracted resources to the destination directory.
            #NOTE: WE WRITE EVERYTHING AS-IF IT'S BINARY.  THE EXTRACT FIG
            #TRANSFORMER SHOULD HANDLE UNIX/WINDOWS LINE ENDINGS...
            for filename, data in resources.get('figures', {}).items():

                #Determine where to write the file to
                dest = os.path.join(self.build_directory, filename)
                
                #Write file
                with io.open(dest, 'wb') as f:
                    f.write(data)

            #Copy referenced files to output directory
            if not destination is None:
                for filename in self.files:

                    #Copy files that match search pattern
                    for matching_filename in glob.glob(filename):
                        shutil.copyfile(matching_filename, 
                                        os.path.join(destination, filename))

            #Determine where to write conversion results.
            dest = notebook_name + '.' + output_extension
            if not destination is None:
                dest = os.path.join(destination, 
                                                    dest)
                
            #Write conversion results.
            with io.open(dest, 'w') as f:
                f.write(output)
