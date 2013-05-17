"""Exporter for the notebook conversion pipeline.

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
from __future__ import print_function, absolute_import

# Stdlib imports
import io
import os
import inspect

# IPython imports
from IPython.config.configurable import Configurable
from IPython.nbformat import current as nbformat
from IPython.utils.traitlets import MetaHasTraits, Unicode, List, Bool
from IPython.utils.text import indent

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader
from markdown import markdown

# local import
import nbconvert.filters.strings
import nbconvert.filters.markdown
import nbconvert.filters.latex
import nbconvert.filters.datatypefilter
import nbconvert.filters.highlight
import nbconvert.filters.ansi

import nbconvert.transformers.extractfigure
import nbconvert.transformers.coalescestreams


#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Standard Jinja2 environment constants
TEMPLATE_PATH = "/../templates/"
TEMPLATE_SKELETON_PATH = "/../templates/skeleton/"

#Jinja2 extensions to load.
JINJA_EXTENSIONS = ['jinja2.ext.loopcontrols']

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
class Exporter(Configurable):
    pre_transformer_order = List(['haspyout_transformer'],
        config=True,
        help= """
            An ordered list of pre-transformer to apply to the IPYNB
            file before running through templates
            """
        )

    template_file = Unicode(
            '', config=True,
            help="Name of the template file to use")

    file_extension = Unicode(
        'txt', config=True, 
        help="Extension of the file that should be written to disk"
        )

    #Extension that the template files use.    
    template_extension = ".tpl"

    #Processors that process the input data prior to the export, set in the 
    #constructor for this class.
    preprocessors = [] 

    # Public Constructor #####################################################
    
    def __init__(self, preprocessors=None, jinja_filters=None, config=None, **kw):
    
        #Call the base class constructor
        super(Exporter, self).__init__(config=config, **kw)

        #Standard environment
        self._init_environment()

        #TODO: Implement reflection style methods to get user transformers.
        #if not preprocessors is None:        
        #    for name in self.pre_transformer_order:
        #        # get the user-defined transformer first
        #        transformer = preprocessors.get(name, getattr(trans, name, None))
        #        if isinstance(transformer, MetaHasTraits):
        #            transformer = transformer(config=config)
        #        self.preprocessors.append(transformer)

        #Add transformers
        self._register_transformers()

        #Add filters to the Jinja2 environment
        self._register_filters()

        #Load user filters.  Overwrite existing filters if need be.
        if not jinja_filters is None:
            for key, user_filter in jinja_filters.iteritems():
                if issubclass(user_filter, MetaHasTraits):
                    self.environment.filters[key] = user_filter(config=config)
                else:
                    self.environment.filters[key] = user_filter
    
    # Public methods #########################################
    
    def from_notebook_node(self, nb):
        nb, resources = self._preprocess(nb)
        
        #Load the template file.
        self.template = self.environment.get_template(self.template_file+self.template_extension)
        
        return self.template.render(nb=nb, resources=resources), resources


    def from_filename(self, filename):
        with io.open(filename) as f:
            return self.from_notebook_node(nbformat.read(f, 'json'))


    def from_file(self, file_stream):
        return self.from_notebook_node(nbformat.read(file_stream, 'json'))


    def register_transformer(self, transformer):
        if inspect.isfunction(transformer):
            self.preprocessors.append(transformer)
            return transformer
        elif isinstance(transformer, MetaHasTraits):
            transformer_instance = transformer(config=self.config)
            self.preprocessors.append(transformer_instance)
            return transformer_instance
        else:
            transformer_instance = transformer()
            self.preprocessors.append(transformer_instance)
            return transformer_instance


    def register_filter(self, name, filter):
        if inspect.isfunction(filter):
            self.environment.filters[name] = filter
        elif isinstance(filter, MetaHasTraits):
            self.environment.filters[name] = filter(config=self.config)
        else:
            self.environment.filters[name] = filter()
        return self.environment.filters[name]


    # Protected and Private methods #########################################
    
    def _register_transformers(self):
        self.register_transformer(nbconvert.transformers.coalescestreams.coalesce_streams)
        
        #Remember the figure extraction transformer so it can be enabled and
        #disabled easily later.
        self.extract_figure_transformer = self.register_transformer(nbconvert.transformers.extractfigure.ExtractFigureTransformer)
        
        
    def _register_filters(self):
        self.register_filter('indent', indent)
        self.register_filter('markdown', markdown)
        self.register_filter('ansi2html', nbconvert.filters.ansi.ansi2html)
        self.register_filter('filter_data_type', nbconvert.filters.datatypefilter.DataTypeFilter)
        self.register_filter('get_lines', nbconvert.filters.strings.get_lines)
        self.register_filter('highlight', nbconvert.filters.highlight.highlight)
        self.register_filter('highlight2html', nbconvert.filters.highlight.highlight) 
        self.register_filter('highlight2latex', nbconvert.filters.highlight.highlight2latex)
        self.register_filter('markdown2latex', nbconvert.filters.markdown.markdown2latex)
        self.register_filter('markdown2rst', nbconvert.filters.markdown.markdown2rst)
        self.register_filter('pycomment', nbconvert.filters.strings.python_comment)
        self.register_filter('rm_ansi', nbconvert.filters.ansi.remove_ansi)
        self.register_filter('rm_dollars', nbconvert.filters.strings.strip_dollars)
        self.register_filter('rm_fake', nbconvert.filters.strings.rm_fake)
        self.register_filter('rm_math_space', nbconvert.filters.latex.rm_math_space)
        self.register_filter('wrap', nbconvert.filters.strings.wrap)
        
        
    def _init_environment(self):
        self.environment = Environment(
            loader=FileSystemLoader([
                os.path.dirname(os.path.realpath(__file__)) + TEMPLATE_PATH,
                os.path.dirname(os.path.realpath(__file__)) + TEMPLATE_SKELETON_PATH,
                ]),
            extensions=JINJA_EXTENSIONS
            )


    def _preprocess(self, nb):

        #Dict of 'resources' that can be filled by the preprocessors.
        resources = {}

        #Run each transformer on the notebook.  Carry the output along
        #to each transformer
        for transformer in self.preprocessors:
            nb, resources = transformer(nb, resources)
        return nb, resources
