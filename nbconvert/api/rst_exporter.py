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

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class RstExporter(exporter.Exporter):

    def __init__(self, preprocessors=None, jinja_filters=None, config=None, **kw):
        
        #Call base class constructor.
        super(exporter.Exporter, self).__init__(preprocessors, jinja_filters, config, **kw)

        #Set defaults
        self.file_extension = "rst"
        self.template_file = "rst"
        self.extract_figure_transformer.enabled = True


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
                    
