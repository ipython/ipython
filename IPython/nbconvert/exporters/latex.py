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
from IPython.utils.traitlets import Unicode, List
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
    
    file_extension = Unicode(
        'tex', config=True, 
        help="Extension of the file that should be written to disk")

    mime_type = Unicode('application/x-tex', config=True,
        help="MIME type of the result file, for HTTP response headers."
        )

    default_template = Unicode('article', config=True, help="""Template of the 
        data format to use.  I.E. 'article' or 'report'""")

    #Latex constants
    default_template_path = Unicode(
        os.path.join("..", "templates", "latex"), config=True,
        help="Path where the template files are located.")

    template_skeleton_path = Unicode(
        os.path.join("..", "templates", "latex", "skeleton"), config=True,
        help="Path where the template skeleton files are located.") 

    #Special Jinja2 syntax that will not conflict when exporting latex.
    jinja_comment_block_start = Unicode("((=", config=True)
    jinja_comment_block_end = Unicode("=))", config=True)
    jinja_variable_block_start = Unicode("(((", config=True)
    jinja_variable_block_end = Unicode(")))", config=True)
    jinja_logic_block_start = Unicode("((*", config=True)
    jinja_logic_block_end = Unicode("*))", config=True)
    
    #Extension that the template files use.    
    template_extension = Unicode(".tplx", config=True)

    def _raw_mimetype_default(self):
        return 'text/latex'


    @property
    def default_config(self):
        c = Config({
            'NbConvertBase': {
                'display_data_priority' : ['latex', 'pdf', 'png', 'jpg', 'svg', 'jpeg', 'text']
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
