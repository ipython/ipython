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

from IPython.utils.traitlets import Integer, List, Bool

from .base import PostProcessorBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class PDFPostProcessor(PostProcessorBase):
    """Writer designed to write to PDF files"""

    iteration_count = Integer(3, config=True, help="""
        How many times pdflatex will be called.
        """)

    command = List(["pdflatex", "{filename}"], config=True, help="""
        Shell command used to compile PDF.""")

    verbose = Bool(False, config=True, help="""
        Whether or not to display the output of the compile call.
        """)

    def call(self, input):
            """
            Consume and write Jinja output a PDF.  
            See files.py for more...
            """        
            command = [c.format(filename=input) for c in self.command]
            self.log.info("Building PDF: %s", command)
            with open(os.devnull, 'rb') as null:
                stdout = subprocess.PIPE if not self.verbose else None
                for index in range(self.iteration_count):
                    p = subprocess.Popen(command, stdout=stdout, stdin=null)
                    out, err = p.communicate()
                    if p.returncode:
                        if self.verbose:
                            # verbose means I didn't capture stdout with PIPE,
                            # so it's already been displayed and `out` is None.
                            out = u''
                        else:
                            out = out.decode('utf-8', 'replace')
                        self.log.critical(u"PDF conversion failed: %s\n%s", command, out)
                        return
