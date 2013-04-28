"""Exporter for the notebook conversion pipeline.

This module defines Exporter, a highly configurable converter
that uses Jinja2 to export notebook files into different format.

You can register both pre-transformers that will act on the notebook format
befor conversion and jinja filter that would then be availlable in the templates
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
from __future__ import print_function, absolute_import

# Stdlib imports
import io
import os
import re

# IPython imports
from IPython.config.configurable import Configurable
from IPython.nbformat import current as nbformat
from IPython.utils.traitlets import MetaHasTraits, Unicode, List, Bool
from IPython.utils.text import indent

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader
from markdown import markdown

# local import (pre-transformers)
from exceptions import ConversionException
from . import transformers as trans #TODO
from .latex_transformer import (LatexTransformer) #TODO
from .utils import  markdown2rst #TODO
from .utils import markdown2latex #TODO
from .utils import highlight2latex #TODO
from .utils import get_lines #TODO
from .utils import remove_ansi #TODO
from .utils import highlight, ansi2html #TODO
from .latex_transformer import rm_math_space #TODO
import .utils.strings as strings

#Jinja2 filters
from .jinja_filters import (python_comment,
    rm_fake,   
     escape_tex, FilterDataType,
    rm_dollars
    )

#Try to import the Sphinx exporter.  If the user doesn't have Sphinx isntalled 
#on his/her machine, fail silently.
try:
    from .sphinx_transformer import (SphinxTransformer) #TODO
except ImportError:
    SphinxTransformer = None

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Standard Jinja2 environment constants
TEMPLATE_PATH = "/../templates/"
TEMPLATE_SKELETON_PATH = "/../templates/skeleton/"
TEMPLATE_EXTENSION = ".tpl"

#Latex Jinja2 constants
LATEX_TEMPLATE_PATH = "/../templates/tex/"
LATEX_TEMPLATE_SKELETON_PATH = "/../templates/tex/skeleton/"
LATEX_TEMPLATE_EXTENSION = ".tplx"

#Special Jinja2 syntax that will not conflict when exporting latex.
LATEX_JINJA_COMMENT_BLOCK = ["((=", "=))"]
LATEX_JINJA_VARIABLE_BLOCK = ["(((", ")))"]
LATEX_JINJA_LOGIC_BLOCK = ["((*", "*))"]

#Jinja2 extensions to load.
JINJA_EXTENSIONS = ['jinja2.ext.loopcontrols']

#Latex substitutions for escaping latex.
LATEX_SUBS = (
    (re.compile(r'\\'), r'\\textbackslash'),
    (re.compile(r'([{}_#%&$])'), r'\\\1'),
    (re.compile(r'~'), r'\~{}'),
    (re.compile(r'\^'), r'\^{}'),
    (re.compile(r'"'), r"''"),
    (re.compile(r'\.\.\.+'), r'\\ldots'),
)

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
class Exporter(Configurable):
    """ A Jinja2 base converter templates

    Preprocess the ipynb files, feed it throug jinja templates,
    and spit an converted files and a data object with other data
    should be mostly configurable
    """

    pre_transformer_order = List(['haspyout_transformer'],
        config=True,
        help= """
            An ordered list of pre transformer to apply to the ipynb
            file before running through templates
            """
        )

    tex_environement = Bool(
        False,
        config=True,
        help=" Whether or not the user is exporting to latex.")

    template_file = Unicode(
            '', config=True,
            help="Name of the template file to use")

    #Processors that process the input data prior to the export, set in the 
    #constructor for this class.
    preprocessors = [] 

    def __init__(self, preprocessors={}, jinja_filters={}, config=None, **kw):
        """ Init a new converter.

        config: the Configurable config object to pass around.

        preprocessors: dict of **availlable** key/value function to run on
                       ipynb json data before conversion to extract/inline file.
                       See `transformer.py` and `ConfigurableTransformers`

                       set the order in which the transformers should apply
                       with the `pre_transformer_order` trait of this class

                       transformers registerd by this key will take precedence on
                       default one.

        jinja_filters: dict of supplementary jinja filter that should be made
                       availlable in template. If those are of Configurable Class type,
                       they will be instanciated with the config object as argument.

                       user defined filter will overwrite the one availlable by default.
        """
        super(ConverterTemplate, self).__init__(config=config, **kw)

        #Create a Latex environment if the user is exporting latex.
        if self.tex_environement:
            self.ext = LATEX_TEMPLATE_EXTENSION
            self.env = Environment(
                loader=FileSystemLoader([
                    os.path.dirname(os.path.realpath(__file__)) + LATEX_TEMPLATE_PATH,
                    os.path.dirname(os.path.realpath(__file__)) + LATEX_TEMPLATE_SKELETON_PATH,
                    ]),
                extensions=JINJA_EXTENSIONS
                )

            #Set special Jinja2 syntax that will not conflict with latex.
            self.env.block_start_string = LATEX_JINJA_LOGIC_BLOCK[0]
            self.env.block_end_string = LATEX_JINJA_LOGIC_BLOCK[1]
            self.env.variable_start_string = LATEX_JINJA_VARIABLE_BLOCK[0]
            self.env.variable_end_string = LATEX_JINJA_VARIABLE_BLOCK[1]
            self.env.comment_start_string = LATEX_JINJA_COMMENT_BLOCK[0]
            self.env.comment_end_string = LATEX_JINJA_COMMENT_BLOCK[1]

        else: #Standard environment
            self.ext = TEMPLATE_EXTENSION
            self.env = Environment(
                loader=FileSystemLoader([
                    os.path.dirname(os.path.realpath(__file__)) + TEMPLATE_PATH,
                    os.path.dirname(os.path.realpath(__file__)) + TEMPLATE_SKELETON_PATH,
                    ]),
                extensions=JINJA_EXTENSIONS
                )

        for name in self.pre_transformer_order:
            # get the user-defined transformer first
            transformer = preprocessors.get(name, getattr(trans, name, None))
            if isinstance(transformer, MetaHasTraits):
                transformer = transformer(config=config)
            self.preprocessors.append(transformer)

        #For compatibility, TODO: remove later.
        self.preprocessors.append(trans.coalesce_streams)
        self.preprocessors.append(trans.ExtractFigureTransformer(config=config))
        self.preprocessors.append(trans.RevealHelpTransformer(config=config))
        self.preprocessors.append(trans.CSSHtmlHeaderTransformer(config=config))
        self.preprocessors.append(LatexTransformer(config=config))

        #Only load the sphinx transformer if the file reference worked 
        #(Sphinx dependencies exist on the user's machine.)
        if SphinxTransformer:
            self.preprocessors.append(SphinxTransformer(config=config))

        #Add filters to the Jinja2 environment
        self.env.filters['filter_data_type'] = FilterDataType(config=config)
        self.env.filters['pycomment'] = _python_comment
        self.env.filters['indent'] = indent
        self.env.filters['rm_fake'] = _rm_fake
        self.env.filters['rm_ansi'] = remove_ansi
        self.env.filters['markdown'] = markdown
        self.env.filters['ansi2html'] = ansi2html
        self.env.filters['markdown2latex'] = markdown2latex
        self.env.filters['markdown2rst'] = markdown2rst
        self.env.filters['get_lines'] = get_lines
        self.env.filters['wrap'] = strings.wrap
        self.env.filters['rm_dollars'] = strings.strip_dollars
        self.env.filters['rm_math_space'] = rm_math_space
        self.env.filters['highlight2html'] = highlight 
        self.env.filters['highlight2latex'] = highlight2latex

        #Latex specific filters
        if self.tex_environement:
            self.env.filters['escape_tex'] = _escape_tex 
            self.env.filters['highlight'] = highlight2latex 
        else:
            self.env.filters['highlight'] = highlight 

        #Load user filters.  Overwrite existing filters if need be.
        for key, user_filter in jinja_filters.iteritems():
            if isinstance(user_filter, MetaHasTraits):
                self.env.filters[key] = user_filter(config=config)
            else:
                self.env.filters[key] = user_filter

        #Load the template file.
        self.template = self.env.get_template(self.template_file+self.ext)


    def export(self, nb):
        """Export notebook object

        nb: Notebook object to export.

        Returns both the converted ipynb file and a dict containing the
        resources created along the way via the transformers and Jinja2
        processing.
        """

        nb, resources = self._preprocess(nb)
        return self.template.render(nb=nb, resources=resources), resources


    def from_filename(self, filename):
        """Read and export a notebook from a filename

        filename: Filename of the notebook file to export.

        Returns both the converted ipynb file and a dict containing the
        resources created along the way via the transformers and Jinja2
        processing.
        """
        with io.open(filename) as f:
            return self.export(nbformat.read(f, 'json'))


    def from_file(self, file_stream):
        """Read and export a notebook from a filename

        file_stream: File handle of file that contains notebook data.

        Returns both the converted ipynb file and a dict containing the
        resources created along the way via the transformers and Jinja2
        processing.
        """

        return self.export(nbformat.read(file_stream, 'json'))


    def _preprocess(self, nb):
        """ Preprocess the notebook using the transformers specific
        for the current export format.

        nb: Notebook to preprocess
        """

        #Dict of 'resources' that can be filled by the preprocessors.
        resources = {}

        #Run each transformer on the notebook.  Carry the output along
        #to each transformer
        for transformer in self.preprocessors:
            nb, resources = transformer(nb, resources)
        return nb, resources


    #TODO: Comment me.
    def _rm_fake(strng):
        return strng.replace('/files/', '')

    #TODO: Comment me.
    def _python_comment(string):
        return '# '+'\n# '.join(string.split('\n'))


    #TODO: Comment me.
    def _escape_tex(value):
        newval = value
        for pattern, replacement in LATEX_SUBS:
            newval = pattern.sub(replacement, newval)
        return newval