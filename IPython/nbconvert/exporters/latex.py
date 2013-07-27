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
from IPython.utils.traitlets import Unicode, List
from IPython.config import Config

from IPython.nbconvert import filters, transformers
from .exporter import Exporter

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class LatexExporter(Exporter):
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

    default_template = Unicode('article', config=True, help="""Template of the 
        data format to use.  I.E. 'full' or 'basic'""")

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


    @property
    def default_config(self):
        c = Config({
            'NbConvertBase': {
                'display_data_priority' : ['latex', 'pdf', 'png', 'jpg', 'svg', 'jpeg', 'text']
                },
             'ExtractOutputTransformer': {
                    'enabled':True
                 },
             'SVG2PDFTransformer': {
                    'enabled':True
                 },
             'LatexTransformer': {
                    'enabled':True
                 },
             'SphinxTransformer': {
                    'enabled':True
                 }
         })
        c.merge(super(LatexExporter,self).default_config)
        return c
