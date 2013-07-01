"""
Exporter that exports Basic HTML.
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

import nbconvert.transformers.csshtmlheader

# local import
import exporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class BasicHtmlExporter(exporter.Exporter):
    """
    Exports a basic HTML document.  This exporter assists with the export of
    HTML.  Inherit from it if you are writing your own HTML template and need
    custom transformers/filters.  If you don't need custom transformers/
    filters, just change the 'template_file' config option.  
    """
    
    file_extension = Unicode(
        'html', config=True, 
        help="Extension of the file that should be written to disk"
        )

    template_file = Unicode(
            'basichtml', config=True,
            help="Name of the template file to use")


    def _register_transformers(self):
        """
        Register all of the transformers needed for this exporter.
        """
        
        #Register the transformers of the base class.
        super(BasicHtmlExporter, self)._register_transformers()
        
        #Register CSSHtmlHeaderTransformer transformer
        self.register_transformer(nbconvert.transformers.csshtmlheader.CSSHtmlHeaderTransformer)
                    
