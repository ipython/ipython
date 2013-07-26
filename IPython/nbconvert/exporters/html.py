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

from IPython.utils.traitlets import Unicode, List

from IPython.nbconvert import transformers
from IPython.config import Config

from .exporter import Exporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class HTMLExporter(Exporter):
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

    default_template = Unicode('full', config=True, help="""Flavor of the data 
        format to use.  I.E. 'full' or 'basic'""")

    @property
    def default_config(self):
        c = Config({
            'CSSHTMLHeaderTransformer':{
                'enabled':True
                }          
            })
        c.merge(super(HTMLExporter,self).default_config)
        return c
