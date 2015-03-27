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

from IPython.config import Config

from .templateexporter import TemplateExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class RSTExporter(TemplateExporter):
    """
    Exports restructured text documents.
    """
    
    def _file_extension_default(self):
        return '.rst'

    def _template_file_default(self):
        return 'rst'

    output_mimetype = 'text/restructuredtext'

    @property
    def default_config(self):
        c = Config({'ExtractOutputPreprocessor':{'enabled':True}})
        c.merge(super(RSTExporter,self).default_config)
        return c
