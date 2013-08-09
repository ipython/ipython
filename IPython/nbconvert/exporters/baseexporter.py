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
import copy
import collections
import datetime


# IPython imports
from IPython.config.configurable import LoggingConfigurable
from IPython.config import Config
from IPython.nbformat import current as nbformat
from IPython.utils.traitlets import MetaHasTraits, Unicode, List
from IPython.utils.importstring import import_item
from IPython.utils import py3compat

from IPython.nbconvert import transformers as nbtransformers


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class ResourcesDict(collections.defaultdict):
    def __missing__(self, key):
        return ''


class BaseExporter(LoggingConfigurable):
    """
    Base Exporter Class that only conver notebook to notebook
    and apply the transformers and provide basic methods for
    reading a notebook from different sources.

    """
    
    # finish the docstring

    file_extension = Unicode(
        'txt', config=True, 
        help="Extension of the file that should be written to disk"
        )

    #Configurability, allows the user to easily add transformers.
    transformers = List(config=True,
        help="""List of transformers, by name or namespace, to enable.""")

    _transformers = None

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


    def __init__(self, config=None, **kw):
        """
        Public constructor
    
        Parameters
        ----------
        config : config
            User configuration instance.
        """
        if not config:
            config = self.default_config
        
        super(BaseExporter, self).__init__(config=config, **kw)

        #Init
        self._init_transformers()


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
        super(BaseExporter, self)._config_changed(name, old, c)


    def from_notebook_node(self, nb, resources=None):
        """
        Convert a notebook from a notebook node instance.
    
        Parameters
        ----------
        nb : Notebook node
        resources : dict (**kw) 
            of additional resources that can be accessed read/write by 
            transformers.
        """
        nb_copy = copy.deepcopy(nb)
        resources = self._init_resources(resources)

        # Preprocess
        nb_copy, resources = self._transform(nb_copy, resources)

        return nb_copy, resources


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
        resources['metadata']['modified_date'] = modified_date.strftime("%B %d, %Y")
        
        with io.open(filename) as f:
            return self.from_notebook_node(nbformat.read(f, 'json'), resources=resources, **kw)


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


    def _init_transformers(self):
        """
        Register all of the transformers needed for this exporter, disabled
        unless specified explicitly.
        """
        if self._transformers is None:
            self._transformers = []

        #Load default transformers (not necessarly enabled by default).
        if self.default_transformers:
            for transformer in self.default_transformers:
                self.register_transformer(transformer)

        #Load user transformers.  Enable by default.
        if self.transformers:
            for transformer in self.transformers:
                self.register_transformer(transformer, enabled=True)
 

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
