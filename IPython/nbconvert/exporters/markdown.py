"""
Exporter that will export your ipynb to Markdown.
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

from IPython.config import Config
from IPython.utils.traitlets import Unicode

from .exporter import Exporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class MarkdownExporter(Exporter):
    """
    Exports to a markdown document (.md)
    """
    
    file_extension = Unicode(
        'md', config=True, 
        help="Extension of the file that should be written to disk")

    @property
    def default_config(self):
        c = Config({'ExtractOutputTransformer':{'enabled':True}})
        c.merge(super(MarkdownExporter,self).default_config)
        return c
