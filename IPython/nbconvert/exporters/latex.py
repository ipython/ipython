"""LaTeX Exporter class"""

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
from IPython.config import Config

from IPython.nbconvert import filters, preprocessors
from .templateexporter import TemplateExporter

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class LatexExporter(TemplateExporter):
    """
    Exports to a Latex template.  Inherit from this class if your template is
    LaTeX based and you need custom tranformers/filters.  Inherit from it if 
    you are writing your own HTML template and need custom tranformers/filters.  
    If you don't need custom tranformers/filters, just change the 
    'template_file' config option.  Place your template in the special "/latex" 
    subfolder of the "../templates" folder.
    """

    def _file_extension_default(self):
        return 'tex'

    def _template_file_default(self):
        return 'article'

    #Latex constants
    def _default_template_path_default(self):
        return os.path.join("..", "templates", "latex")

    def _template_skeleton_path_default(self):
        return os.path.join("..", "templates", "latex", "skeleton")

    #Special Jinja2 syntax that will not conflict when exporting latex.
    jinja_comment_block_start = Unicode("((=", config=True)
    jinja_comment_block_end = Unicode("=))", config=True)
    jinja_variable_block_start = Unicode("(((", config=True)
    jinja_variable_block_end = Unicode(")))", config=True)
    jinja_logic_block_start = Unicode("((*", config=True)
    jinja_logic_block_end = Unicode("*))", config=True)
    
    #Extension that the template files use.    
    template_extension = Unicode(".tplx", config=True)

    output_mimetype = 'text/latex'


    @property
    def default_config(self):
        c = Config({
            'NbConvertBase': {
                'display_data_priority' : ['latex', 'application/pdf', 'png', 'jpg', 'svg', 'jpeg', 'text']
                },
             'ExtractOutputPreprocessor': {
                    'enabled':True
                 },
             'SVG2PDFPreprocessor': {
                    'enabled':True
                 },
             'LatexPreprocessor': {
                    'enabled':True
                 },
             'SphinxPreprocessor': {
                    'enabled':True
                 },
             'HighlightMagicsPreprocessor': {
                    'enabled':True
                 }
         })
        c.merge(super(LatexExporter,self).default_config)
        return c
