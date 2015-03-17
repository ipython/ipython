"""This module defines TemplateExporter, a highly configurable converter
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
import os

# other libs/dependencies are imported at runtime
# to move ImportErrors to runtime when the requirement is actually needed

# IPython imports
from IPython.utils.traitlets import MetaHasTraits, Unicode, List, Dict, Any
from IPython.utils.importstring import import_item
from IPython.utils import py3compat, text

from IPython.nbconvert import filters
from .exporter import Exporter

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
        'highlight2html': filters.Highlight2HTML,
        'highlight2latex': filters.Highlight2Latex,
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
        'wrap_text': filters.wrap_text,
        'escape_latex': filters.escape_latex,
        'citation2latex': filters.citation2latex,
        'path2url': filters.path2url,
        'add_prompts': filters.add_prompts,
        'ascii_only': filters.ascii_only,
        'prevent_list_blocks': filters.prevent_list_blocks,
}

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TemplateExporter(Exporter):
    """
    Exports notebooks into other file formats.  Uses Jinja 2 templating engine
    to output new formats.  Inherit from this class if you are creating a new
    template type along with new filters/preprocessors.  If the filters/
    preprocessors provided by default suffice, there is no need to inherit from
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
        if new == 'default':
            self.template_file = self.default_template
        else:
            self.template_file = new
        self.template = None
        self._load_template()
    
    default_template = Unicode(u'')
    template = Any()
    environment = Any()

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

    filters = Dict(config=True,
        help="""Dictionary of filters, by name and namespace, to add to the Jinja
        environment.""")

    raw_mimetypes = List(config=True,
        help="""formats of raw cells to be included in this Exporter's output."""
    )
    def _raw_mimetypes_default(self):
        return [self.output_mimetype, '']


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
        super(TemplateExporter, self).__init__(config=config, **kw)

        #Init
        self._init_template()
        self._init_environment(extra_loaders=extra_loaders)
        self._init_filters()


    def _load_template(self):
        """Load the Jinja template object from the template file
        
        This is a no-op if the template attribute is already defined,
        or the Jinja environment is not setup yet.
        
        This is triggered by various trait changes that would change the template.
        """
        from jinja2 import TemplateNotFound
        
        if self.template is not None:
            return
        # called too early, do nothing
        if self.environment is None:
            return
        # Try different template names during conversion.  First try to load the
        # template by name with extension added, then try loading the template
        # as if the name is explicitly specified, then try the name as a 
        # 'flavor', and lastly just try to load the template by module name.
        try_names = []
        if self.template_file:
            try_names.extend([
                self.template_file + self.template_extension,
                self.template_file,
            ])
        for try_name in try_names:
            self.log.debug("Attempting to load template %s", try_name)
            try:
                self.template = self.environment.get_template(try_name)
            except (TemplateNotFound, IOError):
                pass
            except Exception as e:
                self.log.warn("Unexpected exception loading template: %s", try_name, exc_info=True)
            else:
                self.log.debug("Loaded template %s", try_name)
                break

    def from_notebook_node(self, nb, resources=None, **kw):
        """
        Convert a notebook from a notebook node instance.
    
        Parameters
        ----------
        nb : :class:`~IPython.nbformat.NotebookNode`
          Notebook node
        resources : dict
          Additional resources that can be accessed read/write by
          preprocessors and filters.
        """
        nb_copy, resources = super(TemplateExporter, self).from_notebook_node(nb, resources, **kw)
        resources.setdefault('raw_mimetypes', self.raw_mimetypes)

        self._load_template()

        if self.template is not None:
            output = self.template.render(nb=nb_copy, resources=resources)
        else:
            raise IOError('template file "%s" could not be found' % self.template_file)
        return output, resources


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
        from jinja2 import Environment, ChoiceLoader, FileSystemLoader
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
