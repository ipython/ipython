"""
Exporter that allows Latex Jinja templates to work.  Contains logic to
appropriately prepare IPYNB files for export to LaTeX.  Including but 
not limited to escaping LaTeX, fixing math region tags, using special
tags to circumvent Jinja/Latex syntax conflicts.
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

# Stdlib imports
import os

# IPython imports
from IPython.utils.traitlets import Unicode

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader

import nbconvert.filters.latex
import nbconvert.filters.highlight
from nbconvert.transformers.latex import LatexTransformer

# local import
import exporter

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Latex Jinja2 constants
LATEX_TEMPLATE_PATH = "/../templates/latex/"
LATEX_TEMPLATE_SKELETON_PATH = "/../templates/latex/skeleton/"

#Special Jinja2 syntax that will not conflict when exporting latex.
LATEX_JINJA_COMMENT_BLOCK = ["((=", "=))"]
LATEX_JINJA_VARIABLE_BLOCK = ["(((", ")))"]
LATEX_JINJA_LOGIC_BLOCK = ["((*", "*))"]

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class LatexExporter(exporter.Exporter):
    """
    Exports to a Latex template.  Inherit from this class if your template is
    LaTeX based and you need custom tranformers/filters.  Inherit from it if 
    you are writing your own HTML template and need custom tranformers/filters.  
    If you don't need custom tranformers/filters, just change the 
    'template_file' config option.  Place your template in the special "/latex" 
    subfolder of the "../templates" folder.
    """
    
    #Extension that the template files use.    
    template_extension = ".tplx"
    
    file_extension = Unicode(
        'tex', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'base', config=True,
            help="Name of the template file to use")
    
    def __init__(self, transformers=None, filters=None, config=None, **kw):
        
        #Call base class constructor.
        super(LatexExporter, self).__init__(transformers, filters, config, **kw)
        
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
        super(LatexExporter, self)._register_filters()

        #Add latex filters to the Jinja2 environment
        self.register_filter('escape_tex', nbconvert.filters.latex.escape_latex) 
        self.register_filter('highlight', nbconvert.filters.highlight.highlight2latex) 
    
    
    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(LatexExporter, self)._register_transformers()
        
        #Register latex transformer
        self.register_transformer(LatexTransformer)
                    