"""restructuredText Exporter class"""

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
from IPython.config import Config

from .templateexporter import TemplateExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class RSTExporter(TemplateExporter):
    """
    Exports restructured text documents.
    """
    
    file_extension = Unicode(
        'rst', config=True, 
        help="Extension of the file that should be written to disk")

    def _raw_mimetype_default(self):
        return 'text/restructuredtext'

    mime_type = Unicode('text/x-rst', config=True,
        help="MIME type of the result file, for HTTP response headers."
        )

    @property
    def default_config(self):
        c = Config({'ExtractOutputPreprocessor':{'enabled':True}})
        c.merge(super(RSTExporter,self).default_config)
        return c
