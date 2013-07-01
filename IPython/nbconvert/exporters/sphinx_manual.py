"""
Exporter for exporting notebooks to Sphinx 'Manual' style latex.  Latex 
formatted for use with PDFLatex.
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

from IPython.utils.traitlets import Unicode

# local import
import sphinx_howto

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SphinxManualExporter(sphinx_howto.SphinxHowtoExporter):
    """
    Exports Sphinx "Manual" LaTeX documents.  The Sphinx "Manual" exporter 
    produces book like latex output for use with PDFLatex. 
    """
    
    template_file = Unicode(
            'sphinx_manual', config=True,
            help="Name of the template file to use")
    