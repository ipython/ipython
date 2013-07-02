"""
Exporter for exporting full HTML documents.
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

from IPython.utils.traitlets import Unicode

from .basichtml import BasicHTMLExporter
from IPython.config import Config

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class FullHTMLExporter(BasicHTMLExporter):
    """
    Exports a full HTML document.
    """

    template_file = Unicode(
            'fullhtml', config=True,
            help="Name of the template file to use")

    @property
    def default_config(self):
        c = Config({'CSSHTMLHeaderTransformer':{'enabled':True}})
        c.merge(super(FullHTMLExporter,self).default_config)
        return c
