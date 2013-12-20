"""Markdown Exporter class"""

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

from .templateexporter import TemplateExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class MarkdownExporter(TemplateExporter):
    """
    Exports to a markdown document (.md)
    """
    
    file_extension = Unicode(
        'md', config=True, 
        help="Extension of the file that should be written to disk")

    output_mimetype = 'text/markdown'
    
    def _raw_mimetypes_default(self):
        return ['text/markdown', 'text/html', '']

    @property
    def default_config(self):
        c = Config({'ExtractOutputPreprocessor':{'enabled':True}})
        c.merge(super(MarkdownExporter,self).default_config)
        return c
