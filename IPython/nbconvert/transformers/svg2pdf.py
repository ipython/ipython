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

import base64
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
INKSCAPE_OSX_COMMAND = '/Applications/Inkscape.app/Contents/Resources/bin/inkscape --without-gui --export-pdf="{to_filename}" "{from_filename}"'


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SVG2PDFTransformer(ConvertFiguresTransformer):
    """
    Converts all of the outputs in a notebook from SVG to PDF.
    """

    from_format = Unicode('svg', config=True, help='Format the converter accepts')
    to_format = Unicode('pdf', config=False, help='Format the converter writes')
    command = Unicode(config=True,
        help="""The command to use for converting SVG to PDF
        
        This string is a template, which will be formatted with the keys
        to_filename and from_filename.
        
        The conversion call must read the SVG from {from_flename},
        and write a PDF to {to_filename}.
        """)
    
    def _command_default(self):
        if sys.platform == "darwin":
            return INKSCAPE_OSX_COMMAND
        elif sys.platform == "win32":
            # windows not yet supported
            return ""
        else:
            return INKSCAPE_COMMAND


    def convert_figure(self, data_format, data):
        """
        Convert a single SVG figure to PDF.  Returns converted data.
        """

        #Work in a temporary directory
        with TemporaryDirectory() as tmpdir:
            
            #Write fig to temp file
            input_filename = os.path.join(tmpdir, 'figure.' + data_format)
            with open(input_filename, 'wb') as f:
                f.write(data)

            #Call conversion application
            output_filename = os.path.join(tmpdir, 'figure.pdf')
            shell = self.command.format(from_filename=input_filename, 
                                   to_filename=output_filename)
            subprocess.call(shell, shell=True) #Shell=True okay since input is trusted.

            #Read output from drive
            # return value expects a filename
            if os.path.isfile(output_filename):
                with open(output_filename, 'rb') as f:
                    # PDF is a nb supported binary, data type, so base64 encode.
                    return base64.encodestring(f.read())
            else:
                return TypeError("Inkscape svg to png conversion failed")
