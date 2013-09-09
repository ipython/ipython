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
import copy
import collections
import datetime

# other libs/dependencies
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, TemplateNotFound

# IPython imports
from IPython.config.configurable import LoggingConfigurable
from IPython.config import Config
from IPython.nbformat import current as nbformat
from IPython.utils.traitlets import MetaHasTraits, DottedObjectName, Unicode, List, Dict, Any
from IPython.utils.importstring import import_item
from IPython.utils import text
from IPython.utils import py3compat

from IPython.nbconvert import transformers as nbtransformers
from IPython.nbconvert import filters

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Jinja2 extensions to load.
JINJA_EXTENSIONS = ['jinja2.ext.loopcontrols']

default_filters = {
        'indent': text.indent,
        'markdown2html': filters.markdown2html,
        'ansi2html': filters.ansi2html,
        'filter_data_type': filters.DataTypeFilter,
        'get_lines': filters.get_lines,
        'highlight2html': filters.highlight2html,
        'highlight2latex': filters.highlight2latex,
        'ipython2python': filters.ipython2python,
        'posix_path': filters.posix_path,
        'markdown2latex': filters.markdown2latex,
        'markdown2rst': filters.markdown2rst,
        'comment_lines': filters.comment_lines,
        'strip_ansi': filters.strip_ansi,
        'strip_dollars': filters.strip_dollars,
        'strip_files_prefix': filters.strip_files_prefix,
        'html2text' : filters.html2text,
        'add_anchor': filters.add_anchor,
        'ansi2latex': filters.ansi2latex,
        'strip_math_space': filters.strip_math_space,
        'wrap_text': filters.wrap_text,
        'escape_latex': filters.escape_latex,
        'path2url': filters.path2url,
}

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class ResourcesDict(collections.defaultdict):
    def __missing__(self, key):
        return ''


class Exporter(LoggingConfigurable):
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


    template_file = Unicode(u'default',
            config=True,
            help="Name of the template file to use")
    def _template_file_changed(self, name, old, new):
        if new=='default':
            self.template_file = self.default_template
        else:
            self.template_file = new
        self.template = None
        self._load_template()
    
    default_template = Unicode(u'')
    template = Any()
    environment = Any()

    file_extension = Unicode(
        'txt', config=True, 
        help="Extension of the file that should be written to disk"
        )

    template_path = List(['.'], config=True)
    def _template_path_changed(self, name, old, new):
        self._load_template()

    default_template_path = Unicode(
        os.path.join("..", "templates"), 
        help="Path where the template files are located.")

    template_skeleton_path = Unicode(
        os.path.join("..", "templates", "skeleton"), 
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
                                 nbtransformers.SVG2PDFTransformer,
                                 nbtransformers.ExtractOutputTransformer,
                                 nbtransformers.CSSHTMLHeaderTransformer,
                                 nbtransformers.RevealHelpTransformer,
                                 nbtransformers.LatexTransformer,
                                 nbtransformers.SphinxTransformer],
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
            ordered list of Jinja loader to find templates. Will be tried in order
            before the default FileSystem ones.
        template : str (optional, kw arg)
            Template to use when exporting.
        """
        if not config:
            config = self.default_config
        
        super(Exporter, self).__init__(config=config, **kw)

        #Init
        self._init_template()
        self._init_environment(extra_loaders=extra_loaders)
        self._init_transformers()
        self._init_filters()


    @property
    def default_config(self):
        return Config()
    
    def _config_changed(self, name, old, new):
        """When setting config, make sure to start with our default_config"""
        c = self.default_config
        if new:
            c.merge(new)
        if c != old:
            self.config = c
        super(Exporter, self)._config_changed(name, old, c)
        

    def _load_template(self):
        """Load the Jinja template object from the template file
        
        This is a no-op if the template attribute is already defined,
        or the Jinja environment is not setup yet.
        
        This is triggered by various trait changes that would change the template.
        """
        if self.template is not None:
            return
        # called too early, do nothing
        if self.environment is None:
            return
        # Try different template names during conversion.  First try to load the
        # template by name with extension added, then try loading the template
        # as if the name is explicitly specified, then try the name as a 
        # 'flavor', and lastly just try to load the template by module name.
        module_name = self.__module__.rsplit('.', 1)[-1]
        try_names = []
        if self.template_file:
            try_names.extend([
                self.template_file + self.template_extension,
                self.template_file,
                module_name + '_' + self.template_file + self.template_extension,
            ])
        try_names.append(module_name + self.template_extension)
        for try_name in try_names:
            self.log.debug("Attempting to load template %s", try_name)
            try:
                self.template = self.environment.get_template(try_name)
            except (TemplateNotFound, IOError):
                pass
            except Exception as e:
                self.log.warn("Unexpected exception loading template: %s", try_name, exc_info=True)
            else:
                self.log.info("Loaded template %s", try_name)
                break
    
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

        # Preprocess
        nb_copy, resources = self._transform(nb_copy, resources)

        self._load_template()

        if self.template is not None:
            output = self.template.render(nb=nb_copy, resources=resources)
        else:
            raise IOError('template file "%s" could not be found' % self.template_file)
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
        if resources is None:
            resources = ResourcesDict()
        if not 'metadata' in resources or resources['metadata'] == '':
            resources['metadata'] = ResourcesDict()
        basename = os.path.basename(filename)
        notebook_name = basename[:basename.rfind('.')]
        resources['metadata']['name'] = notebook_name

        modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
        resources['metadata']['modified_date'] = modified_date.strftime(text.date_format)
        
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


    def register_transformer(self, transformer, enabled=False):
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
        if transformer is None:
            raise TypeError('transformer')
        isclass = isinstance(transformer, type)
        constructed = not isclass

        #Handle transformer's registration based on it's type
        if constructed and isinstance(transformer, py3compat.string_types):
            #Transformer is a string, import the namespace and recursively call
            #this register_transformer method
            transformer_cls = import_item(transformer)
            return self.register_transformer(transformer_cls, enabled)
        
        if constructed and hasattr(transformer, '__call__'):
            #Transformer is a function, no need to construct it.
            #Register and return the transformer.
            if enabled:
                transformer.enabled = True
            self._transformers.append(transformer)
            return transformer

        elif isclass and isinstance(transformer, MetaHasTraits):
            #Transformer is configurable.  Make sure to pass in new default for 
            #the enabled flag if one was specified.
            self.register_transformer(transformer(parent=self), enabled)

        elif isclass:
            #Transformer is not configurable, construct it
            self.register_transformer(transformer(), enabled)

        else:
            #Transformer is an instance of something without a __call__ 
            #attribute.  
            raise TypeError('transformer')


    def register_filter(self, name, jinja_filter):
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
        if jinja_filter is None:
            raise TypeError('filter')
        isclass = isinstance(jinja_filter, type)
        constructed = not isclass

        #Handle filter's registration based on it's type
        if constructed and isinstance(jinja_filter, py3compat.string_types):
            #filter is a string, import the namespace and recursively call
            #this register_filter method
            filter_cls = import_item(jinja_filter)
            return self.register_filter(name, filter_cls)
        
        if constructed and hasattr(jinja_filter, '__call__'):
            #filter is a function, no need to construct it.
            self.environment.filters[name] = jinja_filter
            return jinja_filter

        elif isclass and isinstance(jinja_filter, MetaHasTraits):
            #filter is configurable.  Make sure to pass in new default for 
            #the enabled flag if one was specified.
            filter_instance = jinja_filter(parent=self)
            self.register_filter(name, filter_instance )

        elif isclass:
            #filter is not configurable, construct it
            filter_instance = jinja_filter()
            self.register_filter(name, filter_instance)

        else:
            #filter is an instance of something without a __call__ 
            #attribute.  
            raise TypeError('filter')

        
    def _init_template(self):
        """
        Make sure a template name is specified.  If one isn't specified, try to
        build one from the information we know.
        """
        self._template_file_changed('template_file', self.template_file, self.template_file)
        

    def _init_environment(self, extra_loaders=None):
        """
        Create the Jinja templating environment.
        """
        here = os.path.dirname(os.path.realpath(__file__))
        loaders = []
        if extra_loaders:
            loaders.extend(extra_loaders)

        paths = self.template_path
        paths.extend([os.path.join(here, self.default_template_path),
                      os.path.join(here, self.template_skeleton_path)])
        loaders.append(FileSystemLoader(paths))

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
        for key, value in default_filters.items():
            self.register_filter(key, value)

        #Load user filters.  Overwrite existing filters if need be.
        if self.filters:
            for key, user_filter in self.filters.items():
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
