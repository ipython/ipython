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
import latex_exporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class SphinxExporter(latex_exporter.LatexExporter):

    def __init__(self, preprocessors=None, jinja_filters=None, config=None, sphinx_type="howto", **kw):
        
        #Call base class constructor.
        super(latex_exporter.LatexExporter, self).__init__(preprocessors, jinja_filters, config, **kw)

        #Defaults
        self.template_file = "latex_sphinx_" + sphinx_type

    def _register_filters(self):
        
        #Register the filters of the base class.
        super(latex_exporter.LatexExporter, self)._register_filters()

        #Add latex filters to the Jinja2 environment
        #self.register_filter('escape_tex', filters.latex.escape_tex)  

    
    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(latex_exporter.LatexExporter, self)._register_transformers()
        
        #Register latex transformer
        #self.register_transformer(LatexTransformer)
                    
