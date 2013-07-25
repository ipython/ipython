#!/usr/bin/env python
"""
Contains writer for writing nbconvert output to PDF.
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

import subprocess
import os

from IPython.utils.traitlets import Integer

from .files import FilesWriter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class PDFWriter(FilesWriter):
    """Writer designed to write to PDF files"""

    iteration_count = Integer(3, config=True, help="""
        How many times pdflatex will be called.
        """)

    def write(self, output, resources, notebook_name=None, **kw):
            """
            Consume and write Jinja output a PDF.  
            See files.py for more...
            """        
            dest = super(PDFWriter, self).write(output, resources, notebook_name=notebook_name, **kw)
            command = 'pdflatex ' + dest
            for index in range(self.iteration_count):
                subprocess.Popen(command, shell=True, stdout=open(os.devnull, 'wb'))
