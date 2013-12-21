"""HTML slide show Exporter class"""

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

from IPython.nbconvert import preprocessors
from IPython.config import Config

from .html import HTMLExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SlidesExporter(HTMLExporter):
    """Exports HTML slides with reveal.js"""
    
    def _file_extension_default(self):
        return 'slides.html'

    def _template_file_default(self):
        return 'slides_reveal'

    output_mimetype = 'text/html'

    @property
    def default_config(self):
        c = Config({
            'RevealHelpPreprocessor': {
                'enabled': True,
                },
            })
        c.merge(super(SlidesExporter,self).default_config)
        return c
