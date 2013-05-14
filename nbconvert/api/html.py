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
import exporter
import nbconvert.transformers.csshtmlheader
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class HtmlExporter(exporter.Exporter):

    file_extension = Unicode(
        'html', config=True, 
        help="Extension of the file that should be written to disk"
        )

    template_file = Unicode(
            'fullhtml', config=True,
            help="Name of the template file to use")

    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(HtmlExporter, self)._register_transformers()
        
        #Register latex transformer
        self.register_transformer(nbconvert.transformers.csshtmlheader.CSSHtmlHeaderTransformer)
                    