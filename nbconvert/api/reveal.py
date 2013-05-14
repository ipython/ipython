"""TODO: Docstring
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

# local import
import html
import nbconvert.transformers.revealhelp
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class RevealExporter(html.HtmlExporter):

    file_extension = Unicode(
        'reveal.html', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'reveal', config=True,
            help="Name of the template file to use")
    
    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(RevealExporter, self)._register_transformers()
        
        #Register reveal help transformer
        self.register_transformer(nbconvert.transformers.revealhelp.RevealHelpTransformer)
        