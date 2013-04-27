"""Base classes for the notebook conversion pipeline.

This module defines ConverterTemplate, a highly configurable converter
that uses Jinja2 to convert notebook files into different format.

You can register both pre-transformers that will act on the notebook format
befor conversion and jinja filter that would then be availlable in the templates
"""

from __future__ import absolute_import

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

from __future__ import print_function
from __future__ import absolute_import

# Stdlib imports
import io
import os

# IPython imports
from IPython.utils.traitlets import MetaHasTraits
from IPython.utils.traitlets import (Unicode, List, Bool)
from IPython.config.configurable import Configurable
from IPython.nbformat import current as nbformat


# other libs/dependencies
from jinja2 import Environment, FileSystemLoader


# local import (pre-transformers)
from  . import transformers as trans
try:
    from .sphinx_transformer import (SphinxTransformer)
except ImportError:
    SphinxTransformer = None

from .latex_transformer import (LatexTransformer)

# some jinja filters
from .jinja_filters import (python_comment, indent,
        rm_fake, remove_ansi, markdown, highlight, highlight2latex,
        ansi2html, markdown2latex, get_lines, escape_tex, FilterDataType,
        rm_dollars, rm_math_space
        )

from .utils import  markdown2rst

import textwrap

def wrap(text, width=100):
    """ try to detect and wrap paragraph"""
    splitt = text.split('\n')
    wrp = map(lambda x:textwrap.wrap(x,width),splitt)
    wrpd = map('\n'.join, wrp)
    return '\n'.join(wrpd)



# define differents environemnt with different
# delimiters not to conflict with languages inside

env = Environment(
        loader=FileSystemLoader([
            os.path.dirname(os.path.realpath(__file__))+'/../templates/',
            os.path.dirname(os.path.realpath(__file__))+'/../templates/skeleton/',
            ]),
        extensions=['jinja2.ext.loopcontrols']
        )


texenv = Environment(
        loader=FileSystemLoader([
            os.path.dirname(os.path.realpath(__file__))+'/../templates/tex/',
            os.path.dirname(os.path.realpath(__file__))+'/../templates/skeleton/tex/',
            ]),
        extensions=['jinja2.ext.loopcontrols']
        )


texenv.block_start_string = '((*'
texenv.block_end_string = '*))'

texenv.variable_start_string = '((('
texenv.variable_end_string = ')))'

texenv.comment_start_string = '((='
texenv.comment_end_string = '=))'

texenv.filters['escape_tex'] = escape_tex

#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------
class ConversionException(Exception):
    pass

class ConverterTemplate(Configurable):
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

    tex_environement = Bool(False,
            config=True,
            help=""" is this a tex environment or not """)

    template_file = Unicode('',
            config=True,
            help=""" Name of the template file to use """ )
    #-------------------------------------------------------------------------
    # Instance-level attributes that are set in the constructor for this
    # class.
    #-------------------------------------------------------------------------


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

        # variable parameters depending on the pype of jinja environement
        self.env = texenv  if self.tex_environement else env
        self.ext = '.tplx' if self.tex_environement else '.tpl'

        for name in self.pre_transformer_order:
            # get the user-defined transformer first
            transformer = preprocessors.get(name, getattr(trans, name, None))
            if isinstance(transformer, MetaHasTraits):
                transformer = transformer(config=config)
            self.preprocessors.append(transformer)

        ## for compat, remove later
        self.preprocessors.append(trans.coalesce_streams)
        self.preprocessors.append(trans.ExtractFigureTransformer(config=config))
        self.preprocessors.append(trans.RevealHelpTransformer(config=config))
        self.preprocessors.append(trans.CSSHtmlHeaderTransformer(config=config))
        if SphinxTransformer:
            self.preprocessors.append(SphinxTransformer(config=config))
        self.preprocessors.append(LatexTransformer(config=config))

        ##
        self.env.filters['filter_data_type'] = FilterDataType(config=config)
        self.env.filters['pycomment'] = python_comment
        self.env.filters['indent'] = indent
        self.env.filters['rm_fake'] = rm_fake
        self.env.filters['rm_ansi'] = remove_ansi
        self.env.filters['markdown'] = markdown
        self.env.filters['highlight'] = highlight2latex if self.tex_environement else highlight 
        self.env.filters['highlight2html'] = highlight 
        self.env.filters['highlight2latex'] = highlight2latex
        self.env.filters['ansi2html'] = ansi2html
        self.env.filters['markdown2latex'] = markdown2latex
        self.env.filters['markdown2rst'] = markdown2rst
        self.env.filters['get_lines'] = get_lines
        self.env.filters['wrap'] = wrap
        self.env.filters['rm_dollars'] = rm_dollars
        self.env.filters['rm_math_space'] = rm_math_space

        ## user  filter will overwrite
        for key, filtr in jinja_filters.iteritems():
            if isinstance(filtr, MetaHasTraits):
                self.env.filters[key] = filtr(config=config)
            else :
                self.env.filters[key] = filtr

        self.template = self.env.get_template(self.template_file+self.ext)


    def process(self, nb):
        """
        preprocess the notebook json for easier use with the templates.
        will call all the `preprocessor`s in order before returning it.
        """

        # dict of 'resources' that could be made by the preprocessors
        # like key/value data to extract files from ipynb like in latex conversion
        resources = {}

        for preprocessor in self.preprocessors:
            nb, resources = preprocessor(nb, resources)

        return nb, resources

    def convert(self, nb):
        """ convert the ipynb file

        return both the converted ipynb file and a dict containing potential
        other resources
        """
        nb, resources = self.process(nb)
        return self.template.render(nb=nb, resources=resources), resources


    def from_filename(self, filename):
        """read and convert a notebook from a file name"""
        with io.open(filename) as f:
            return self.convert(nbformat.read(f, 'json'))

    def from_file(self, filelike):
        """read and convert a notebook from a filelike object

        filelike object will just be "read" and should be json format..
        """
        return self.convert(nbformat.read(filelike, 'json'))

    def from_json(self, json):
        """ not implemented

        Should convert from a json object
        """
        raise NotImplementedError('not implemented (yet?)')
