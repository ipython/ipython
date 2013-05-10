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
import transformers.csshtmlheader

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class HtmlExporter(exporter.Exporter):

    def __init__(self, preprocessors=None, jinja_filters=None, config=None, full_html=True, **kw):
        
        #Call base class constructor.
        super(exporter.Exporter, self).__init__(preprocessors, jinja_filters, config, **kw)

        #Set defaults
        self.file_extension = "html"  
        self.extract_figure_transformer.enabled = True
        
        #Load the correct template
        if full_html:
            self.template_file = "fullhtml"
        else:
            self.template_file = "basichtml"
    
    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(exporter.Exporter, self)._register_transformers()
        
        #Register latex transformer
        self.register_transformer(transformers.csshtmlheader.CSSHtmlHeaderTransformer)
                    