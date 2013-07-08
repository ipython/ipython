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
import types
from copy import deepcopy

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader
from markdown import markdown

# IPython imports
from IPython.config.configurable import Configurable
from IPython.config import Config
from IPython.nbformat import current as nbformat
from IPython.utils.import_string import import_item
from IPython.utils.traitlets import MetaHasTraits, Unicode, DottedObjectName, List
from IPython.utils.text import indent

from IPython.nbconvert import filters
from IPython.nbconvert import transformers

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Jinja2 extensions to load.
JINJA_EXTENSIONS = ['jinja2.ext.loopcontrols']

default_filters = {
        'indent': indent,
        'markdown': markdown,
        'ansi2html': filters.ansi2html,
        'filter_data_type': filters.DataTypeFilter,
        'get_lines': filters.get_lines,
        'highlight': filters.highlight,
        'highlight2html': filters.highlight,
        'highlight2latex': filters.highlight2latex,
        'markdown2latex': filters.markdown2latex,
        'markdown2rst': filters.markdown2rst,
        'pycomment': filters.python_comment,
        'rm_ansi': filters.remove_ansi,
        'rm_dollars': filters.strip_dollars,
        'rm_fake': filters.rm_fake,
        'ansi2latex': filters.ansi2latex,
        'rm_math_space': filters.rm_math_space,
        'wrap': filters.wrap
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
        os.path.join("..", "templates"), config=True,
        help="Path where the template files are located.")

    template_skeleton_path = Unicode(
        os.path.join("..", "templates", "skeleton"), config=True,
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

    #Configurability, allows the user to easily add filters and transformers.
    transformers = List(config=True,
        """List of transformers, by name or namespace, to enable.""")
    filters = Dict(config=True,
        """Dictionary of filters, by name and namespace, to add to the Jinja
        environment.""")

    
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
        self._transformers = []
        for transformer in self.transformers:
            self.register_transformer(transformer)
                
        #Load user filters.  Overwrite existing filters if need be.
        for key, user_filter in self.filters.iteritems():
            self.register_filter(key, user_filter)


    @property
    def default_config(self):
        return Config()
    
    
    def from_notebook_node(self, notebook_name, nb, resources=None):
        """
        Convert a notebook from a notebook node instance.
    
        Parameters
        ----------
        notebook_name : str
            Name of the notebook (unique).  Used to prefix extracted figure 
            filenames.  Must be passed in to exporter so the templates can know
            the names of the files the extracted figures are stored in.  
            (ugly, I know... but necessary for building multiple notebooks to 
                one directory)
        nb : Notebook node
        resources : a dict of additional resources that
                can be accessed read/write by transformers
                and filters.
        """

        if resources is None:
            resources = {}
        nb, resources = self._preprocess(notebook_name, nb, resources)
        
        #Load the template file.
        self.template = self.environment.get_template(self.template_file + self.template_extension)
        
        return self.template.render(nb=nb, resources=resources), resources


    def from_filename(self, filename, notebook_name=None):
        """
        Convert a notebook from a notebook file.
    
        Parameters
        ----------
        filename : str
            Full filename of the notebook file to open and convert.
        """

        #Get the notebook name by removing the full path to the notebook and 
        #the extension on the notebook.
        if notebook_name is None:
            basename = os.path.basename(filename)
            notebook_name = basename[:basename.rfind('.')]

        with io.open(filename) as f:
            return self.from_notebook_node(notebook_name, nbformat.read(f, 'json'))


    def from_file(self, notebook_name, file_stream):
        """
        Convert a notebook from a notebook file.
    
        Parameters
        ----------
        notebook_name : str
            Name of the notebook (unique).  Used to prefix extracted figure 
            filenames.  Must be passed in to exporter so the templates can know
            the names of the files the extracted figures are stored in.  
            (ugly, I know... but necessary for building multiple notebooks to 
                one directory)
        file_stream : file-like object
            Notebook file-like object to convert.
        """
        return self.from_notebook_node(notebook_name, nbformat.read(file_stream, 'json'))


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
        if self._transformers is None:
            self._transformers = []
        
        if inspect.isfunction(transformer):
            self._transformers.append(transformer)
            return transformer
        elif isinstance(transformer, types.StringTypes):
            transformer_cls = import_item(DottedObjectName(transformer))
            return self.register_transformer(transformer_cls)
        elif isinstance(transformer, MetaHasTraits):
            transformer_instance = transformer(config=self.config)
            self._transformers.append(transformer_instance)
            return transformer_instance
        else:
            transformer_instance = transformer()
            self._transformers.append(transformer_instance)
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
        elif isinstance(filter, types.StringTypes):
            fliter_cls = import_item(DottedObjectName(filter))
            self.register_filter(name, filter_cls)
        elif isinstance(filter, MetaHasTraits):
            self.environment.filters[name] = filter(config=self.config)
        else:
            self.environment.filters[name] = filter()
        return self.environment.filters[name]

    
    def _register_transformers(self):
        """
        Register all of the transformers needed for this exporter.
        """
         
        self.register_transformer(transformers.coalesce_streams)
        
        #Remember the figure extraction transformer so it can be enabled and
        #disabled easily later.
        self.extract_figure_transformer = self.register_transformer(transformers.ExtractFigureTransformer)
        

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
        here = os.path.dirname(os.path.realpath(__file__))
        self.environment = Environment(
            loader=FileSystemLoader([
                os.path.join(here, self.template_path),
                os.path.join(here, self.template_skeleton_path),
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


    def _preprocess(self, notebook_name, nb, resources):
        """
        Preprocess the notebook before passing it into the Jinja engine.
        To preprocess the notebook is to apply all of the 
    
        Parameters
        ----------
        notebook_name : string
            Name of the notebook
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
        for transformer in self._transformers:
            nbc, resc = transformer(notebook_name, nbc, resc)

        return nbc, resc
