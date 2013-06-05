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

# IPython imports
from IPython.utils.traitlets import Unicode
from IPython.config import Config

# other libs/dependencies
import nbconvert.filters.latex
import nbconvert.filters.highlight
from nbconvert.transformers.latex import LatexTransformer

# local import
import exporter

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
    
    file_extension = Unicode(
        'tex', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
        'base', config=True,
        help="Name of the template file to use")

    #Latex constants
    template_path = Unicode(
        "/../templates/latex/", config=True,
        help="Path where the template files are located.")

    template_skeleton_path = Unicode(
        "/../templates/latex/skeleton/", config=True,
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

    _default_config = Config({
             'display_data_priority' : ['latex', 'svg', 'png', 'jpg', 'jpeg' , 'text'],
             'extra_ext_map':{'svg':'pdf'},
             'ExtractFigureTransformer' : Config({'enabled':True})
         })
    
    def __init__(self, transformers=None, filters=None, config=None, **kw):
        """
        Public constructor
    
        Parameters
        ----------
        transformers : list[of transformer]
            Custom transformers to apply to the notebook prior to engaging
            the Jinja template engine.  Any transformers specified here
            will override existing transformers if a naming conflict
            occurs.
        filters : list[of filter]
            Custom filters to make accessible to the Jinja templates.  Any
            filters specified here will override existing filters if a
            naming conflict occurs.
        config : config
            User configuration instance.
        """
        
        #Call base class constructor.

        c = self.default_config
        if config :
            c.merge(Config(config))

        super(LatexExporter, self).__init__(transformers, filters, config=c, **kw)
        
        #self.extract_figure_transformer.extra_ext_map={'svg':'pdf'}

        
    def _register_filters(self):
        """
        Register all of the filters required for the exporter.
        """
        
        #Register the filters of the base class.
        super(LatexExporter, self)._register_filters()

        #Add latex filters to the Jinja2 environment
        self.register_filter('escape_tex', nbconvert.filters.latex.escape_latex) 
        self.register_filter('highlight', nbconvert.filters.highlight.highlight2latex) 
    
    
    def _register_transformers(self):
        """
        Register all of the transformers needed for this exporter.
        """
        
        #Register the transformers of the base class.
        super(LatexExporter, self)._register_transformers()
        
        #Register latex transformer
        self.register_transformer(LatexTransformer)

