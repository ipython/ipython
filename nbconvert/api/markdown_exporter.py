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
class MarkdownExporter(exporter.Exporter):

    def __init__(self, preprocessors=None, jinja_filters=None, config=None, **kw):
        
        #Call base class constructor.
        super(exporter.Exporter, self).__init__(preprocessors, jinja_filters, config, **kw)

        #Set defaults
        self.file_extension = "md"  
        self.extract_figure_transformer.enabled = True
        self.template_file = "markdown"
