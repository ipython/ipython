"""This module defines Exporter, a highly configurable converter
that uses Jinja2 to export notebook files into different formats.
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
from copy import deepcopy

# IPython imports
from IPython.config.configurable import Configurable
from IPython.config import Config
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

#Jinja2 extensions to load.
JINJA_EXTENSIONS = ['jinja2.ext.loopcontrols']

default_filters = {
        'indent': indent,
        'markdown': markdown,
        'ansi2html': nbconvert.filters.ansi.ansi2html,
        'filter_data_type': nbconvert.filters.datatypefilter.DataTypeFilter,
        'get_lines': nbconvert.filters.strings.get_lines,
        'highlight': nbconvert.filters.highlight.highlight,
        'highlight2html': nbconvert.filters.highlight.highlight,
        'highlight2latex': nbconvert.filters.highlight.highlight2latex,
        'markdown2latex': nbconvert.filters.markdown.markdown2latex,
        'markdown2rst': nbconvert.filters.markdown.markdown2rst,
        'pycomment': nbconvert.filters.strings.python_comment,
        'rm_ansi': nbconvert.filters.ansi.remove_ansi,
        'rm_dollars': nbconvert.filters.strings.strip_dollars,
        'rm_fake': nbconvert.filters.strings.rm_fake,
        'ansi2latex': nbconvert.filters.ansi.ansi2latex,
        'rm_math_space': nbconvert.filters.latex.rm_math_space,
        'wrap': nbconvert.filters.strings.wrap
}

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class Exporter(Configurable):
    """
    Exports notebooks into other file formats.  Uses Jinja 2 templating engine
    to output new formats.  Inherit from this class if you are creating a new
    template type along with new filters/transformers.  If the filters/
    transformers provided by default suffice, there is no need to inherit from
    this class.  Instead, override the template_file and file_extension
    traits via a config file.
    
    {filters}
    """
    
    # finish the docstring
    __doc__ = __doc__.format(filters = '- '+'\n    - '.join(default_filters.keys()))


    template_file = Unicode(
            '', config=True,
            help="Name of the template file to use")

    file_extension = Unicode(
        'txt', config=True, 
        help="Extension of the file that should be written to disk"
        )

    template_path = Unicode(
        "/../templates/", config=True,
        help="Path where the template files are located.")

    template_skeleton_path = Unicode(
        "/../templates/skeleton/", config=True,
        help="Path where the template skeleton files are located.") 

    #Jinja block definitions
    jinja_comment_block_start = Unicode("", config=True)
    jinja_comment_block_end = Unicode("", config=True)
    jinja_variable_block_start = Unicode("", config=True)
    jinja_variable_block_end = Unicode("", config=True)
    jinja_logic_block_start = Unicode("", config=True)
    jinja_logic_block_end = Unicode("", config=True)
    
    #Extension that the template files use.    
    template_extension = Unicode(".tpl", config=True)

    #Processors that process the input data prior to the export, set in the 
    #constructor for this class.
    transformers = None

    
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
        filters : dict[of filter]
            filters specified here will override existing filters if a naming
            conflict occurs. Filters are availlable in jinja template through
            the name of the corresponding key. Cf class docstring for
            availlable default filters.
        config : config
            User configuration instance.
        """
        
        #Call the base class constructor
        c = self.default_config
        if config:
            c.merge(config)

        super(Exporter, self).__init__(config=c, **kw)

        #Standard environment
        self._init_environment()

        #Add transformers
        self._register_transformers()

        #Add filters to the Jinja2 environment
        self._register_filters()

        #Load user transformers.  Overwrite existing transformers if need be.
        if transformers :
            for transformer in transformers:
                self.register_transformer(transformer)
                
        #Load user filters.  Overwrite existing filters if need be.
        if not filters is None:
            for key, user_filter in filters.iteritems():
                if issubclass(user_filter, MetaHasTraits):
                    self.environment.filters[key] = user_filter(config=config)
                else:
                    self.environment.filters[key] = user_filter

    @property
    def default_config(self):
        return Config()

    
    
    def from_notebook_node(self, nb, resources=None):
        """
        Convert a notebook from a notebook node instance.
    
        Parameters
        ----------
        nb : Notebook node
        resources : a dict of additional resources that
                can be accessed read/write by transformers
                and filters.
        """
        if resources is None:
            resources = {}
        nb, resources = self._preprocess(nb, resources)
        
        #Load the template file.
        self.template = self.environment.get_template(self.template_file+self.template_extension)
        
        return self.template.render(nb=nb, resources=resources), resources


    def from_filename(self, filename):
        """
        Convert a notebook from a notebook file.
    
        Parameters
        ----------
        filename : str
            Full filename of the notebook file to open and convert.
        """
        
        with io.open(filename) as f:
            return self.from_notebook_node(nbformat.read(f, 'json'))


    def from_file(self, file_stream):
        """
        Convert a notebook from a notebook file.
    
        Parameters
        ----------
        file_stream : file-like object
            Notebook file-like object to convert.
        """
        return self.from_notebook_node(nbformat.read(file_stream, 'json'))


    def register_transformer(self, transformer):
        """
        Register a transformer.
        Transformers are classes that act upon the notebook before it is
        passed into the Jinja templating engine.  Transformers are also
        capable of passing additional information to the Jinja
        templating engine.
    
        Parameters
        ----------
        transformer : transformer
        """
        if self.transformers is None:
            self.transformers = []
        
        if inspect.isfunction(transformer):
            self.transformers.append(transformer)
            return transformer
        elif isinstance(transformer, MetaHasTraits):
            transformer_instance = transformer(config=self.config)
            self.transformers.append(transformer_instance)
            return transformer_instance
        else:
            transformer_instance = transformer()
            self.transformers.append(transformer_instance)
            return transformer_instance


    def register_filter(self, name, filter):
        """
        Register a filter.
        A filter is a function that accepts and acts on one string.  
        The filters are accesible within the Jinja templating engine.
    
        Parameters
        ----------
        name : str
            name to give the filter in the Jinja engine
        filter : filter
        """
        if inspect.isfunction(filter):
            self.environment.filters[name] = filter
        elif isinstance(filter, MetaHasTraits):
            self.environment.filters[name] = filter(config=self.config)
        else:
            self.environment.filters[name] = filter()
        return self.environment.filters[name]

    
    def _register_transformers(self):
        """
        Register all of the transformers needed for this exporter.
        """
         
        self.register_transformer(nbconvert.transformers.coalescestreams.coalesce_streams)
        
        #Remember the figure extraction transformer so it can be enabled and
        #disabled easily later.
        self.extract_figure_transformer = self.register_transformer(nbconvert.transformers.extractfigure.ExtractFigureTransformer)
        
        
    def _register_filters(self):
        """
        Register all of the filters required for the exporter.
        """
        for k, v in default_filters.iteritems():
            self.register_filter(k, v)
        
        
    def _init_environment(self):
        """
        Create the Jinja templating environment.
        """
        
        self.environment = Environment(
            loader=FileSystemLoader([
                os.path.dirname(os.path.realpath(__file__)) + self.template_path,
                os.path.dirname(os.path.realpath(__file__)) + self.template_skeleton_path,
                ]),
            extensions=JINJA_EXTENSIONS
            )
        
        #Set special Jinja2 syntax that will not conflict with latex.
        if self.jinja_logic_block_start:
            self.environment.block_start_string = self.jinja_logic_block_start
        if self.jinja_logic_block_end:
            self.environment.block_end_string = self.jinja_logic_block_end
        if self.jinja_variable_block_start:
            self.environment.variable_start_string = self.jinja_variable_block_start
        if self.jinja_variable_block_end:
            self.environment.variable_end_string = self.jinja_variable_block_end
        if self.jinja_comment_block_start:
            self.environment.comment_start_string = self.jinja_comment_block_start
        if self.jinja_comment_block_end:
            self.environment.comment_end_string = self.jinja_comment_block_end


    def _preprocess(self, nb, resources):
        """
        Preprocess the notebook before passing it into the Jinja engine.
        To preprocess the notebook is to apply all of the 
    
        Parameters
        ----------
        nb : notebook node
            notebook that is being exported.
        resources : a dict of additional resources that
            can be accessed read/write by transformers
            and filters.
        """
        
        # Do a deepcopy first, 
        # we are never safe enough with what the transformers could do.
        nbc =  deepcopy(nb)
        resc = deepcopy(resources)
        #Run each transformer on the notebook.  Carry the output along
        #to each transformer
        for transformer in self.transformers:
            nb, resources = transformer(nbc, resc)
        return nb, resources

