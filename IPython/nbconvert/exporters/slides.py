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

from IPython.utils.traitlets import Unicode

from IPython.nbconvert import preprocessors
from IPython.config import Config

from .html import HTMLExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SlidesExporter(HTMLExporter):
    """Exports HTML slides with reveal.js"""
    
    file_extension = Unicode(
        'slides.html', config=True, 
        help="Extension of the file that should be written to disk"
        )

    output_mimetype = 'text/html'

    default_template = Unicode('reveal', config=True, help="""Template of the 
        data format to use.  I.E. 'reveal'""")

    @property
    def default_config(self):
        c = Config({
            'RevealHelpPreprocessor': {
                'enabled': True,
                },
            })
        c.merge(super(SlidesExporter,self).default_config)
        return c
