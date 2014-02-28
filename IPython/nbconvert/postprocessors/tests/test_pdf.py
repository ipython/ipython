"""
Module with tests for the PDF post-processor
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

import logging
import os

from IPython.testing import decorators as dec

from ...tests.base import TestsBase
from ..pdf import PDFPostProcessor


#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

HELLO_WORLD = r"""% hello.tex - Our first LaTeX example!
\documentclass{article}
\begin{document}
Hello World!
\end{document}"""


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestPDF(TestsBase):
    """Contains test functions for pdf.py"""


    def test_constructor(self):
        """Can a PDFPostProcessor be constructed?"""
        PDFPostProcessor()


    @dec.onlyif_cmds_exist('pdflatex')
    def test_pdf(self):
        """Can a PDF be made using the PDFPostProcessor?"""

        # Work in a temporary directory with hello world latex in it.
        with self.create_temp_cwd():
            with open('a.tex', 'w') as f:
                f.write(HELLO_WORLD)

            # Construct post-processor
            processor = PDFPostProcessor(log=logging.getLogger())
            processor.verbose = False
            processor('a.tex')

            # Check that the PDF was created.
            assert os.path.isfile('a.pdf')
            
            # Make sure that temp files are cleaned up
            for ext in processor.temp_file_exts:
                assert not os.path.isfile('a'+ext)
