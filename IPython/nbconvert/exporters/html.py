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

import os

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
    
    def _file_extension_default(self):
        return 'html'

    def _default_template_path_default(self):
        return os.path.join("..", "templates", "html")

    def _template_file_default(self):
        return 'full'
    
    output_mimetype = 'text/html'
    
    @property
    def default_config(self):
        c = Config({
            'NbConvertBase': {
                'display_data_priority' : ['javascript', 'html', 'application/pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg' , 'text']
                },
            'CSSHTMLHeaderPreprocessor':{
                'enabled':True
                },
            'HighlightMagicsPreprocessor': {
                'enabled':True
                }
            })
        c.merge(super(HTMLExporter,self).default_config)
        return c
