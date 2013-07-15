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
import copy
import collections
import datetime

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader, ChoiceLoader

# IPython imports
from IPython.config.configurable import Configurable
from IPython.config import Config
from IPython.nbformat import current as nbformat
from IPython.utils.traitlets import MetaHasTraits, DottedObjectName, Unicode, List, Dict
from IPython.utils.importstring import import_item
from IPython.utils.text import indent

from IPython.nbconvert import transformers as nbtransformers
from IPython.nbconvert import filters

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Jinja2 extensions to load.
JINJA_EXTENSIONS = ['jinja2.ext.loopcontrols']

default_filters = {
        'indent': indent,
        'markdown': filters.markdown2html,
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

class ResourcesDict(collections.defaultdict):
    def __missing__(self, key):
        return ''


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
        help="""List of transformers, by name or namespace, to enable.""")

    filters = Dict(config=True,
        help="""Dictionary of filters, by name and namespace, to add to the Jinja
        environment.""")

    default_transformers = List([nbtransformers.coalesce_streams,
                                 nbtransformers.ExtractFigureTransformer],
        config=True,
        help="""List of transformers available by default, by name, namespace, 
        instance, or type.""")
    
    def __init__(self, config=None, extra_loaders=None, **kw):
        """
        Public constructor
    
        Parameters
        ----------
        config : config
            User configuration instance.
        extra_loaders : list[of Jinja Loaders]
            ordered list of Jinja loder to find templates. Will be tried in order
            before the default FileSysteme ones.
        """
        
        #Call the base class constructor
        c = self.default_config
        if config:
            c.merge(config)

        super(Exporter, self).__init__(config=c, **kw)

        #Init
        self._init_environment(extra_loaders=extra_loaders)
        self._init_transformers()
        self._init_filters()


    @property
    def default_config(self):
        return Config()

    
    def from_notebook_node(self, nb, resources=None, **kw):
        """
        Convert a notebook from a notebook node instance.
    
        Parameters
        ----------
        nb : Notebook node
        resources : dict (**kw) 
            of additional resources that can be accessed read/write by 
            transformers and filters.
        """
        nb_copy = copy.deepcopy(nb)
        resources = self._init_resources(resources)

        #Preprocess
        nb_copy, resources = self._transform(nb_copy, resources)

        #Convert
        self.template = self.environment.get_template(self.template_file + self.template_extension)
        output = self.template.render(nb=nb_copy, resources=resources)
        return output, resources


    def from_filename(self, filename, resources=None, **kw):
        """
        Convert a notebook from a notebook file.
    
        Parameters
        ----------
        filename : str
            Full filename of the notebook file to open and convert.
        """

        #Pull the metadata from the filesystem.
        if not 'metadata' in resources:
            resources['metadata'] = ResourcesDict()
        basename = os.path.basename(filename)
        notebook_name = basename[:basename.rfind('.')]
        resources['metadata']['name'] = notebook_name

        modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
        resources['metadata']['modified_date'] = modified_date.strftime("%B %-d, %Y")
        
        with io.open(filename) as f:
            return self.from_notebook_node(nbformat.read(f, 'json'), resources=resources,**kw)


    def from_file(self, file_stream, resources=None, **kw):
        """
        Convert a notebook from a notebook file.
    
        Parameters
        ----------
        file_stream : file-like object
            Notebook file-like object to convert.
        """
        return self.from_notebook_node(nbformat.read(file_stream, 'json'), resources=resources, **kw)


    def register_transformer(self, transformer, enabled=None):
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

        #Handle transformer's registration based on it's type
        if inspect.isfunction(transformer):
            #Transformer is a function, no need to construct it.
            self._transformers.append(transformer)
            return transformer

        elif isinstance(transformer, types.StringTypes):
            #Transformer is a string, import the namespace and recursively call
            #this register_transformer method
            transformer_cls = import_item(DottedObjectName(transformer))
            return self.register_transformer(transformer_cls, enabled=None)

        elif isinstance(transformer, MetaHasTraits):
            #Transformer is configurable.  Make sure to pass in new default for 
            #the enabled flag if one was specified.
            transformer_instance = transformer(parent=self)
            if enabled is not None:
                transformer_instance.enabled = True

        else:
            #Transformer is not configurable, construct it
            transformer_instance = transformer()

        #Register and return the transformer.
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
            filter_cls = import_item(DottedObjectName(filter))
            self.register_filter(name, filter_cls)
        elif isinstance(filter, MetaHasTraits):
            self.environment.filters[name] = filter(config=self.config)
        else:
            self.environment.filters[name] = filter()
        return self.environment.filters[name]

        
    def _init_environment(self, extra_loaders=None):
        """
        Create the Jinja templating environment.
        """
        here = os.path.dirname(os.path.realpath(__file__))
        loaders = []
        if extra_loaders:
            loaders.extend(extra_loaders)

        loaders.append(FileSystemLoader([
                os.path.join(here, self.template_path),
                os.path.join(here, self.template_skeleton_path),
                ]))

        self.environment = Environment(
            loader= ChoiceLoader(loaders),
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

    
    def _init_transformers(self):
        """
        Register all of the transformers needed for this exporter, disabled
        unless specified explicitly.
        """
        self._transformers = []

        #Load default transformers (not necessarly enabled by default).
        if self.default_transformers:
            for transformer in self.default_transformers:
                self.register_transformer(transformer)

        #Load user transformers.  Enable by default.
        if self.transformers:
            for transformer in self.transformers:
                self.register_transformer(transformer, enabled=True)
 

    def _init_filters(self):
        """
        Register all of the filters required for the exporter.
        """
        
        #Add default filters to the Jinja2 environment
        for key, value in default_filters.iteritems():
            self.register_filter(key, value)

        #Load user filters.  Overwrite existing filters if need be.
        if self.filters:
            for key, user_filter in self.filters.iteritems():
                self.register_filter(key, user_filter)


    def _init_resources(self, resources):

        #Make sure the resources dict is of ResourcesDict type.
        if resources is None:
            resources = ResourcesDict()
        if not isinstance(resources, ResourcesDict):
            new_resources = ResourcesDict()
            new_resources.update(resources)
            resources = new_resources 

        #Make sure the metadata extension exists in resources
        if 'metadata' in resources:
            if not isinstance(resources['metadata'], ResourcesDict):
                resources['metadata'] = ResourcesDict(resources['metadata'])
        else:
            resources['metadata'] = ResourcesDict()
            if not resources['metadata']['name']: 
                resources['metadata']['name'] = 'Notebook'

        #Set the output extension
        resources['output_extension'] = self.file_extension
        return resources
        

    def _transform(self, nb, resources):
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
        
        # Do a copy.deepcopy first, 
        # we are never safe enough with what the transformers could do.
        nbc =  copy.deepcopy(nb)
        resc = copy.deepcopy(resources)

        #Run each transformer on the notebook.  Carry the output along
        #to each transformer
        for transformer in self._transformers:
            nbc, resc = transformer(nbc, resc)
        return nbc, resc
