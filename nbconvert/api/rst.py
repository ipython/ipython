"""TODO: Docstring
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

# local import
import exporter
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class RstExporter(exporter.Exporter):

    file_extension = Unicode(
        'rst', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'rst', config=True,
            help="Name of the template file to use")
    
    def _register_filters(self):
        
        #Register the filters of the base class.
        super(exporter.Exporter, self)._register_filters()

        #Add latex filters to the Jinja2 environment
        #self.register_filter('escape_tex', filters.latex.escape_tex)  

    
    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(exporter.Exporter, self)._register_transformers()
        
        #Register latex transformer
        #self.register_transformer(LatexTransformer)
                    
