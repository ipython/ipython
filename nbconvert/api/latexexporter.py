 """Latex exporter for the notebook conversion pipeline.

This module defines Exporter, a highly configurable converter
that uses Jinja2 to export notebook files into different format.

You can register both pre-transformers that will act on the notebook format
before conversion and jinja filter that would then be available in the templates
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
import io
import os

# IPython imports
from IPython.config.configurable import Configurable
from IPython.nbformat import current as nbformat
from IPython.utils.traitlets import MetaHasTraits, Unicode, List, Bool
from IPython.utils.text import indent

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader
from markdown import markdown

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
LATEX_TEMPLATE_EXTENSION = ".tplx"

#Special Jinja2 syntax that will not conflict when exporting latex.
LATEX_JINJA_COMMENT_BLOCK = ["((=", "=))"]
LATEX_JINJA_VARIABLE_BLOCK = ["(((", ")))"]
LATEX_JINJA_LOGIC_BLOCK = ["((*", "*))"]

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
class LatexExporter(exporter.Exporter):
    """ A Jinja2 latex exporter

    Preprocess the ipynb files, feed it through jinja templates,
    and spit an converted files and a data object with other data
    should be mostly configurable
    """

    def __init__(self, preprocessors=None, jinja_filters=None, config=None, **kw):
        """ Init a new converter.

        config: the Configurable config object to pass around.

        preprocessors: dict of **available** key/value function to run on
                       ipynb json data before conversion to extract/inline file.
                       See `transformer.py` and `ConfigurableTransformers`

                       set the order in which the transformers should apply
                       with the `pre_transformer_order` trait of this class

                       transformers registerd by this key will take precedence on
                       default one.

        jinja_filters: dict of supplementary jinja filter that should be made
                       available in template. If those are of Configurable Class type,
                       they will be instanciated with the config object as argument.

                       user defined filter will overwrite the one available by default.
        """

        #Call the base class constructor
        super(exporter.Exporter, self).__init__(preprocessors, jinja_filters, config, **kw)


    def _init_environment(self):
        self.ext = LATEX_TEMPLATE_EXTENSION
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
                    