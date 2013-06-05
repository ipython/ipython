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

# local import
import exporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class RstExporter(exporter.Exporter):
    """
    Exports restructured text documents.
    """
    
    file_extension = Unicode(
        'rst', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'rst', config=True,
            help="Name of the template file to use")

    _default_config = Config({'ExtractFigureTransformer':{'enabled':True}}) 


    def __init__(self, transformers=None, filters=None, config=None, **kw):
       
        c = self.default_config
        if config :
            c.merge(config)
        
        super(RstExporter, self).__init__(transformers=transformers,
                                                filters=filters,
                                                config=c,
                                                **kw)
                    
