"""
Reveal slide show exporter.
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
from IPython.config import Config

from .basichtml import BasicHTMLExporter
from IPython.nbconvert import transformers

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class RevealExporter(BasicHTMLExporter):
    """
    Exports a Reveal slide show (.HTML) which may be rendered in a web browser.
    """
    
    file_extension = Unicode(
        'reveal.html', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'reveal', config=True,
            help="Name of the template file to use")


    @property
    def default_config(self):
        c = Config({
            'CSSHTMLHeaderTransformer':{
                'enabled':True
                },
            'RevealHelpTransformer':{
                'enabled':True,
                },                
            })
        c.merge(super(RevealExporter,self).default_config)
        return c
