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
import html_exporter
import transformers.revealhelp

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class RevealExporter(html_exporter.HtmlExporter):

    def __init__(self, preprocessors=None, jinja_filters=None, config=None, **kw):
        
        #Call base class constructor.
        super(html_exporter.HtmlExporter, self).__init__(preprocessors, jinja_filters, config, **kw)

        #Set defaults
        self.file_extension = "reveal.html"
        self.template_file = "reveal"

    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(html_exporter.HtmlExporter, self)._register_transformers()
        
        #Register reveal help transformer
        self.register_transformer(transformers.revealhelp.RevealHelpTransformer)
        