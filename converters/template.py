"""Base classes for the notebook conversion pipeline.

This module defines Converter, from which all objects designed to implement
a conversion of IPython notebooks to some other format should inherit.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import print_function, absolute_import
import converters.transformers as trans
from converters.jinja_filters import (python_comment, indent,
        rm_fake, remove_ansi, markdown, highlight,
        ansi2html, markdown2latex, escape_tex, FilterDataType)

from converters.utils import  markdown2rst



# Stdlib imports
import io

from IPython.utils.traitlets import MetaHasTraits

from jinja2 import Environment, FileSystemLoader
env = Environment(
        loader=FileSystemLoader([
            './templates/',
            './templates/skeleton/',
            ]),
        extensions=['jinja2.ext.loopcontrols']
        )

texenv = Environment(
        loader=FileSystemLoader([
            './templates/tex/',
            './templates/skeleton/tex/',
            ]),
        extensions=['jinja2.ext.loopcontrols']
        )

# IPython imports
from IPython.nbformat import current as nbformat
from IPython.config.configurable import Configurable
from IPython.utils.traitlets import ( Unicode, List, Bool)

#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------
class ConversionException(Exception):
    pass



texenv.block_start_string = '((*'
texenv.block_end_string = '*))'

texenv.variable_start_string = '((('
texenv.variable_end_string = ')))'

texenv.comment_start_string = '((='
texenv.comment_end_string = '=))'

texenv.filters['escape_tex'] = escape_tex


class ConverterTemplate(Configurable):
    """ A Jinja2 base converter templates

    Preprocess the ipynb files, feed it throug jinja templates,
    and spit an converted files and a data object with other data

    shoudl be mostly configurable
    """

    pre_transformer_order = List(['haspyout_transformer'],
            config=True,
              help= """
                    An ordered list of pre transformer to apply to the ipynb
                    file befor running through templates
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


        config: the Configurable confgg object to pass around

        preprocessors: dict of **availlable** key/value function to run on
        ipynb json data before conversion to extract/inline file,

        jinja_filter : dict of supplementary jinja filter that should be made
        availlable in template. If those are of Configurable Class type, they
        will be instanciated with the config object as argument.

        """
        super(ConverterTemplate, self).__init__(config=config, **kw)
        self.env = texenv  if self.tex_environement else env
        self.ext = '.tplx' if self.tex_environement else '.tpl'

        for name in self.pre_transformer_order:
            transformer = getattr(preprocessors, name, getattr(trans, name, None))
            if isinstance(transformer, MetaHasTraits):
                transformer = transformer(config=config)
            self.preprocessors.append(transformer)

        ## for compat, remove later
        self.preprocessors.append(trans.ExtractFigureTransformer(config=config))
        self.preprocessors.append(trans.RevealHelpTransformer(config=config))
        self.preprocessors.append(trans.CSSHtmlHeaderTransformer(config=config))

        ##
        self.env.filters['filter_data_type'] = FilterDataType(config=config)
        self.env.filters['pycomment'] = python_comment
        self.env.filters['indent'] = indent
        self.env.filters['rm_fake'] = rm_fake
        self.env.filters['rm_ansi'] = remove_ansi
        self.env.filters['markdown'] = markdown
        self.env.filters['highlight'] = highlight
        self.env.filters['ansi2html'] = ansi2html
        self.env.filters['markdown2latex'] = markdown2latex
        self.env.filters['markdown2rst'] = markdown2rst
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
        "read and parse notebook into NotebookNode called self.nb"
        with io.open(filename) as f:
            return self.convert(nbformat.read(f, 'json'))



