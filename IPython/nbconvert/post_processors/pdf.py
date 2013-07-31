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

from IPython.utils.traitlets import Integer, Unicode, Bool

from .base import PostProcessorBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class PDFPostProcessor(PostProcessorBase):
    """Writer designed to write to PDF files"""

    iteration_count = Integer(3, config=True, help="""
        How many times pdflatex will be called.
        """)

    compiler = Unicode(u'pdflatex {0}', config=True, help="""
        Shell command used to compile PDF.""")

    verbose = Bool(False, config=True, help="""
        Whether or not to display the output of the compile call.
        """)

    def call(self, input):
            """
            Consume and write Jinja output a PDF.  
            See files.py for more...
            """        
            command = self.compiler.format(input)
            self.log.info("Building PDF: `%s`", command)
            for index in range(self.iteration_count):
                if self.verbose:
                    subprocess.Popen(command, shell=True)
                else:
                    with open(os.devnull, 'wb') as null:
                        subprocess.Popen(command, shell=True, stdout=null)
