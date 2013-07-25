"""
Exporter for exporting notebooks to restructured text.
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
from IPython.config import Config

from .exporter import Exporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class RSTExporter(Exporter):
    """
    Exports restructured text documents.
    """
    
    file_extension = Unicode(
        'rst', config=True, 
        help="Extension of the file that should be written to disk")

    @property
    def default_config(self):
        c = Config({'ExtractOutputTransformer':{'enabled':True}})
        c.merge(super(RSTExporter,self).default_config)
        return c
