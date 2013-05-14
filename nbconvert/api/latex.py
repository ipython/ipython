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

# Stdlib imports
import os

# IPython imports
from IPython.utils.traitlets import Unicode

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader

# local import
import exporter
import filters.latex
import filters.pygments
from transformers.latex import LatexTransformer
#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Latex Jinja2 constants
LATEX_TEMPLATE_PATH = "/../templates/tex/"
LATEX_TEMPLATE_SKELETON_PATH = "/../templates/tex/skeleton/"

#Special Jinja2 syntax that will not conflict when exporting latex.
LATEX_JINJA_COMMENT_BLOCK = ["((=", "=))"]
LATEX_JINJA_VARIABLE_BLOCK = ["(((", ")))"]
LATEX_JINJA_LOGIC_BLOCK = ["((*", "*))"]

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
class LatexExporter(exporter.Exporter):

    #Extension that the template files use.    
    template_extension = ".tplx"
    
    file_extension = Unicode(
        'tex', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'latex_base', config=True,
            help="Name of the template file to use")
    
    def __init__(self, preprocessors=None, jinja_filters=None, config=None, **kw):
        
        #Call base class constructor.
        super(exporter.Exporter, self).__init__(preprocessors, jinja_filters, config, **kw)
        
        self.extract_figure_transformer.display_data_priority = ['latex', 'svg', 'png', 'jpg', 'jpeg' , 'text']
        self.extract_figure_transformer.extra_ext_map={'svg':'pdf'}
        
        
    def _init_environment(self):
        self.environment = Environment(
            loader=FileSystemLoader([
                os.path.dirname(os.path.realpath(__file__)) + LATEX_TEMPLATE_PATH,
                os.path.dirname(os.path.realpath(__file__)) + LATEX_TEMPLATE_SKELETON_PATH,
                ]),
            extensions=exporter.JINJA_EXTENSIONS
            )

        #Set special Jinja2 syntax that will not conflict with latex.
        self.environment.block_start_string = LATEX_JINJA_LOGIC_BLOCK[0]
        self.environment.block_end_string = LATEX_JINJA_LOGIC_BLOCK[1]
        self.environment.variable_start_string = LATEX_JINJA_VARIABLE_BLOCK[0]
        self.environment.variable_end_string = LATEX_JINJA_VARIABLE_BLOCK[1]
        self.environment.comment_start_string = LATEX_JINJA_COMMENT_BLOCK[0]
        self.environment.comment_end_string = LATEX_JINJA_COMMENT_BLOCK[1]
        
        
    def _register_filters(self):
        
        #Register the filters of the base class.
        super(exporter.Exporter, self)._register_filters()

        #Add latex filters to the Jinja2 environment
        self.register_filter('escape_tex', filters.latex.escape_tex) 
        self.register_filter('highlight', filters.pygments.highlight2latex) 
    
    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(exporter.Exporter, self)._register_transformers()
        
        #Register latex transformer
        self.register_transformer(LatexTransformer)
                    