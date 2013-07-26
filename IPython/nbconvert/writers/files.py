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
import glob

from IPython.utils.traitlets import Unicode
from IPython.utils.path import link_or_copy

from .base import WriterBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class FilesWriter(WriterBase):
    """Consumes nbconvert output and produces files."""


    build_directory = Unicode(".", config=True, 
                              help="""Directory to write output to.  Leave blank
                              to output to the current directory""")


    # Make sure that the output directory exists.
    def _build_directory_changed(self, name, old, new):
        if new and not os.path.isdir(new):
            os.makedirs(new)


    def __init__(self, **kw):
        super(FilesWriter, self).__init__(**kw)
        self._build_directory_changed('build_directory', self.build_directory, 
                                      self.build_directory)


    def write(self, output, resources, notebook_name=None, **kw):
            """
            Consume and write Jinja output to the file system.  Output directory
            is set via the 'build_directory' variable of this instance (a 
            configurable).

            See base for more...
            """

            # Pull the extension and subdir from the resources dict.
            output_extension = resources['output_extension']

            # Write all of the extracted resources to the destination directory.
            # NOTE: WE WRITE EVERYTHING AS-IF IT'S BINARY.  THE EXTRACT FIG
            # TRANSFORMER SHOULD HANDLE UNIX/WINDOWS LINE ENDINGS...
            for filename, data in resources.get('outputs', {}).items():

                # Determine where to write the file to
                dest = os.path.join(self.build_directory, filename)
                path = os.path.dirname(dest)
                if not os.path.isdir(path):
                    os.makedirs(path)

                # Write file
                with io.open(dest, 'wb') as f:
                    f.write(data)

            # Copy referenced files to output directory
            if self.build_directory:
                for filename in self.files:

                    # Copy files that match search pattern
                    for matching_filename in glob.glob(filename):

                        # Make sure folder exists.
                        dest = os.path.join(self.build_directory, filename)
                        path = os.path.dirname(dest)
                        if not os.path.isdir(path):
                            os.makedirs(path)

                        # Copy if destination is different.
                        if not os.path.normpath(dest) == os.path.normpath(matching_filename):
                            link_or_copy(matching_filename, dest)

            # Determine where to write conversion results.
            dest = notebook_name + '.' + output_extension
            if self.build_directory:
                dest = os.path.join(self.build_directory, dest)

            # Write conversion results.
            with io.open(dest, 'w') as f:
                f.write(output)
