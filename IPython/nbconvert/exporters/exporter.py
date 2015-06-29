"""This module defines a base Exporter class. For Jinja template-based export,
see templateexporter.py.
"""


from __future__ import print_function, absolute_import

import io
import os
import copy
import collections
import datetime

from IPython.config.configurable import LoggingConfigurable
from IPython.config import Config
from IPython import nbformat
from IPython.utils.traitlets import MetaHasTraits, Unicode, List, TraitError
from IPython.utils.importstring import import_item
from IPython.utils import text, py3compat


class ResourcesDict(collections.defaultdict):
    def __missing__(self, key):
        return ''


class FilenameExtension(Unicode):
    """A trait for filename extensions."""

    default_value = u''
    info_text = 'a filename extension, beginning with a dot'

    def validate(self, obj, value):
        # cast to proper unicode
        value = super(FilenameExtension, self).validate(obj, value)

        # check that it starts with a dot
        if value and not value.startswith('.'):
            msg = "FileExtension trait '{}' does not begin with a dot: {!r}"
            raise TraitError(msg.format(self.name, value))

        return value


class Exporter(LoggingConfigurable):
    """
    Class containing methods that sequentially run a list of preprocessors on a 
    NotebookNode object and then return the modified NotebookNode object and 
    accompanying resources dict.
    """

    file_extension = FilenameExtension(
        '.txt', config=True,
        help="Extension of the file that should be written to disk"
        )

    # MIME type of the result file, for HTTP response headers.
    # This is *not* a traitlet, because we want to be able to access it from
    # the class, not just on instances.
    output_mimetype = ''

    #Configurability, allows the user to easily add filters and preprocessors.
    preprocessors = List(config=True,
        help="""List of preprocessors, by name or namespace, to enable.""")

    _preprocessors = List()

    default_preprocessors = List([
                                  'IPython.nbconvert.preprocessors.ClearOutputPreprocessor',
                                  'IPython.nbconvert.preprocessors.ExecutePreprocessor',
                                  'IPython.nbconvert.preprocessors.coalesce_streams',
                                  'IPython.nbconvert.preprocessors.SVG2PDFPreprocessor',
                                  'IPython.nbconvert.preprocessors.CSSHTMLHeaderPreprocessor',
                                  'IPython.nbconvert.preprocessors.RevealHelpPreprocessor',
                                  'IPython.nbconvert.preprocessors.LatexPreprocessor',
                                  'IPython.nbconvert.preprocessors.HighlightMagicsPreprocessor',
                                  'IPython.nbconvert.preprocessors.ExtractOutputPreprocessor',
                                 ],
        config=True,
        help="""List of preprocessors available by default, by name, namespace, 
        instance, or type.""")


    def __init__(self, config=None, **kw):
        """
        Public constructor

        Parameters
        ----------
        config : config
            User configuration instance.
        """
        with_default_config = self.default_config
        if config:
            with_default_config.merge(config)
        
        super(Exporter, self).__init__(config=with_default_config, **kw)

        self._init_preprocessors()


    @property
    def default_config(self):
        return Config()

    def from_notebook_node(self, nb, resources=None, **kw):
        """
        Convert a notebook from a notebook node instance.

        Parameters
        ----------
        nb : :class:`~IPython.nbformat.NotebookNode`
          Notebook node (dict-like with attr-access)
        resources : dict
          Additional resources that can be accessed read/write by
          preprocessors and filters.
        **kw
          Ignored (?)
        """
        nb_copy = copy.deepcopy(nb)
        resources = self._init_resources(resources)
        
        if 'language' in nb['metadata']:
            resources['language'] = nb['metadata']['language'].lower()

        # Preprocess
        nb_copy, resources = self._preprocess(nb_copy, resources)

        return nb_copy, resources


    def from_filename(self, filename, resources=None, **kw):
        """
        Convert a notebook from a notebook file.

        Parameters
        ----------
        filename : str
            Full filename of the notebook file to open and convert.
        """

        # Pull the metadata from the filesystem.
        if resources is None:
            resources = ResourcesDict()
        if not 'metadata' in resources or resources['metadata'] == '':
            resources['metadata'] = ResourcesDict()
        path, basename = os.path.split(filename)
        notebook_name = basename[:basename.rfind('.')]
        resources['metadata']['name'] = notebook_name
        resources['metadata']['path'] = path

        modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
        resources['metadata']['modified_date'] = modified_date.strftime(text.date_format)

        with io.open(filename, encoding='utf-8') as f:
            return self.from_notebook_node(nbformat.read(f, as_version=4), resources=resources, **kw)


    def from_file(self, file_stream, resources=None, **kw):
        """
        Convert a notebook from a notebook file.

        Parameters
        ----------
        file_stream : file-like object
            Notebook file-like object to convert.
        """
        return self.from_notebook_node(nbformat.read(file_stream, as_version=4), resources=resources, **kw)


    def register_preprocessor(self, preprocessor, enabled=False):
        """
        Register a preprocessor.
        Preprocessors are classes that act upon the notebook before it is
        passed into the Jinja templating engine.  preprocessors are also
        capable of passing additional information to the Jinja
        templating engine.

        Parameters
        ----------
        preprocessor : preprocessor
        """
        if preprocessor is None:
            raise TypeError('preprocessor')
        isclass = isinstance(preprocessor, type)
        constructed = not isclass

        # Handle preprocessor's registration based on it's type
        if constructed and isinstance(preprocessor, py3compat.string_types):
            # Preprocessor is a string, import the namespace and recursively call
            # this register_preprocessor method
            preprocessor_cls = import_item(preprocessor)
            return self.register_preprocessor(preprocessor_cls, enabled)

        if constructed and hasattr(preprocessor, '__call__'):
            # Preprocessor is a function, no need to construct it.
            # Register and return the preprocessor.
            if enabled:
                preprocessor.enabled = True
            self._preprocessors.append(preprocessor)
            return preprocessor

        elif isclass and isinstance(preprocessor, MetaHasTraits):
            # Preprocessor is configurable.  Make sure to pass in new default for 
            # the enabled flag if one was specified.
            self.register_preprocessor(preprocessor(parent=self), enabled)

        elif isclass:
            # Preprocessor is not configurable, construct it
            self.register_preprocessor(preprocessor(), enabled)

        else:
            # Preprocessor is an instance of something without a __call__ 
            # attribute.  
            raise TypeError('preprocessor')


    def _init_preprocessors(self):
        """
        Register all of the preprocessors needed for this exporter, disabled
        unless specified explicitly.
        """
        self._preprocessors = []

        # Load default preprocessors (not necessarly enabled by default).
        for preprocessor in self.default_preprocessors:
            self.register_preprocessor(preprocessor)

        # Load user-specified preprocessors.  Enable by default.
        for preprocessor in self.preprocessors:
            self.register_preprocessor(preprocessor, enabled=True)


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
                new_metadata = ResourcesDict()
                new_metadata.update(resources['metadata'])
                resources['metadata'] = new_metadata
        else:
            resources['metadata'] = ResourcesDict()
            if not resources['metadata']['name']:
                resources['metadata']['name'] = 'Notebook'

        #Set the output extension
        resources['output_extension'] = self.file_extension
        return resources


    def _preprocess(self, nb, resources):
        """
        Preprocess the notebook before passing it into the Jinja engine.
        To preprocess the notebook is to apply all of the

        Parameters
        ----------
        nb : notebook node
            notebook that is being exported.
        resources : a dict of additional resources that
            can be accessed read/write by preprocessors
        """

        # Do a copy.deepcopy first,
        # we are never safe enough with what the preprocessors could do.
        nbc =  copy.deepcopy(nb)
        resc = copy.deepcopy(resources)

        #Run each preprocessor on the notebook.  Carry the output along
        #to each preprocessor
        for preprocessor in self._preprocessors:
            nbc, resc = preprocessor(nbc, resc)
        return nbc, resc
