"""HTML Exporter class"""

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

from IPython.utils.traitlets import Unicode, List

from IPython.nbconvert import preprocessors
from IPython.config import Config

from .templateexporter import TemplateExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class HTMLExporter(TemplateExporter):
    """
    Exports a basic HTML document.  This exporter assists with the export of
    HTML.  Inherit from it if you are writing your own HTML template and need
    custom preprocessors/filters.  If you don't need custom preprocessors/
    filters, just change the 'template_file' config option.  
    """
    
    file_extension = Unicode(
        'html', config=True, 
        help="Extension of the file that should be written to disk"
        )

    mime_type = Unicode('text/html', config=True,
        help="MIME type of the result file, for HTTP response headers."
        )

    default_template = Unicode('full', config=True, help="""Flavor of the data 
        format to use.  I.E. 'full' or 'basic'""")
    
    def _output_mimetype_default(self):
        return 'text/html'
    
    @property
    def default_config(self):
        c = Config({
            'CSSHTMLHeaderPreprocessor':{
                'enabled':True
                },
            'HighlightMagicsPreprocessor': {
                'enabled':True
                }
            })
        c.merge(super(HTMLExporter,self).default_config)
        return c
