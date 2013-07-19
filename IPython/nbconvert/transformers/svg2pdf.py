"""Module containing a transformer that converts outputs in the notebook from 
one format to another.
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

import os
import sys
import subprocess

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import Unicode

from .convertfigures import ConvertFiguresTransformer


#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

INKSCAPE_COMMAND = 'inkscape --without-gui --export-pdf="{to_filename}" "{from_filename}"'
#INKSCAPE_OSX_COMMAND = '/Applications/Inkscape.app/Contents/Resources/bin/inkscape --without-gui --export-pdf="{to_filename}" "{from_filename}"'


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SVG2PDFTransformer(ConvertFiguresTransformer):
    """
    Converts all of the outputs in a notebook from one format to another.
    """

    from_format = Unicode('svg', config=True, help='Format the converter accepts')
    to_format = Unicode('pdf', config=False, help='Format the converter writes')


    def convert_figure(self, data_format, data):
        """
        Convert a single Svg figure.  Returns converted data.
        """

        #Work in a temporary directory
        with TemporaryDirectory() as tmpdir:
            
            #Write fig to temp file
            input_filename = os.path.join(tmpdir, 'figure.' + data_format)
            with open(input_filename, 'w') as f:
                f.write(data)

            #Determine command (different on Mac OSX)
            command = INKSCAPE_COMMAND 
            if sys.platform == 'darwin':
                command = INKSCAPE_OSX_COMMAND

            #Call conversion application
            output_filename = os.path.join(tmpdir, 'figure.pdf')
            shell = command.format(from_filename=input_filename, 
                                   to_filename=output_filename)
            subprocess.call(shell, shell=True) #Shell=True okay since input is trusted.

            #Read output from drive
            if os.path.isfile(output_filename):
                with open(output_filename, 'rb') as f:
                    return f.read().encode("base64") #PDF is a nb supported binary
                                                     #data type, so base64 encode.
            else:
                return TypeError("Inkscape svg to png conversion failed")
