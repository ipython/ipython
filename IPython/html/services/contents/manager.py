"""A base class for contents managers."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from fnmatch import fnmatch
import itertools
import os

from tornado.web import HTTPError

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current, sign
from IPython.utils.traitlets import Instance, Unicode, List


class ContentsManager(LoggingConfigurable):
    """Base class for serving files and directories.

    This serves any text or binary file,
    as well as directories,
    with special handling for JSON notebook documents.

    Most APIs take a path argument,
    which is always an API-style unicode path,
    and always refers to a directory.

    - unicode, not url-escaped
    - '/'-separated
    - leading and trailing '/' will be stripped
    - if unspecified, path defaults to '',
      indicating the root path.

    name is also unicode, and refers to a specfic target:

    - unicode, not url-escaped
    - must not contain '/'
    - It refers to an individual filename
    - It may refer to a directory name,
      in the case of listing or creating directories.

    """

    notary = Instance(sign.NotebookNotary)
    def _notary_default(self):
        return sign.NotebookNotary(parent=self)

    hide_globs = List(Unicode, [
            u'__pycache__', '*.pyc', '*.pyo',
            '.DS_Store', '*.so', '*.dylib', '*~',
        ], config=True, help="""
        Glob patterns to hide in file and directory listings.
    """)

    untitled_notebook = Unicode("Untitled", config=True,
        help="The base name used when creating untitled notebooks."
    )

    untitled_file = Unicode("untitled", config=True,
        help="The base name used when creating untitled files."
    )

    untitled_directory = Unicode("Untitled Folder", config=True,
        help="The base name used when creating untitled directories."
    )

    # ContentsManager API part 1: methods that must be
    # implemented in subclasses.

    def path_exists(self, path):
        """Does the API-style path (directory) actually exist?

        Like os.path.isdir

        Override this method in subclasses.

        Parameters
        ----------
        path : string
            The path to check

        Returns
        -------
        exists : bool
            Whether the path does indeed exist.
        """
        raise NotImplementedError

    def is_hidden(self, path):
        """Does the API style path correspond to a hidden directory or file?

        Parameters
        ----------
        path : string
            The path to check. This is an API path (`/` separated,
            relative to root dir).

        Returns
        -------
        hidden : bool
            Whether the path is hidden.

        """
        raise NotImplementedError

    def file_exists(self, name, path=''):
        """Does a file exist at the given name and path?

        Like os.path.isfile

        Override this method in subclasses.

        Parameters
        ----------
        name : string
            The name of the file you are checking.
        path : string
            The relative path to the file's directory (with '/' as separator)

        Returns
        -------
        exists : bool
            Whether the file exists.
        """
        raise NotImplementedError('must be implemented in a subclass')

    def exists(self, name, path=''):
        """Does a file or directory exist at the given name and path?

        Like os.path.exists

        Parameters
        ----------
        name : string
            The name of the file you are checking.
        path : string
            The relative path to the file's directory (with '/' as separator)

        Returns
        -------
        exists : bool
            Whether the target exists.
        """
        return self.file_exists(name, path) or self.path_exists("%s/%s" % (path, name))

    def get_model(self, name, path='', content=True):
        """Get the model of a file or directory with or without content."""
        raise NotImplementedError('must be implemented in a subclass')

    def save(self, model, name, path=''):
        """Save the file or directory and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def update(self, model, name, path=''):
        """Update the file or directory and return the model with no content.

        For use in PATCH requests, to enable renaming a file without
        re-uploading its contents. Only used for renaming at the moment.
        """
        raise NotImplementedError('must be implemented in a subclass')

    def delete(self, name, path=''):
        """Delete file or directory by name and path."""
        raise NotImplementedError('must be implemented in a subclass')

    def create_checkpoint(self, name, path=''):
        """Create a checkpoint of the current state of a file

        Returns a checkpoint_id for the new checkpoint.
        """
        raise NotImplementedError("must be implemented in a subclass")

    def list_checkpoints(self, name, path=''):
        """Return a list of checkpoints for a given file"""
        return []

    def restore_checkpoint(self, checkpoint_id, name, path=''):
        """Restore a file from one of its checkpoints"""
        raise NotImplementedError("must be implemented in a subclass")

    def delete_checkpoint(self, checkpoint_id, name, path=''):
        """delete a checkpoint for a file"""
        raise NotImplementedError("must be implemented in a subclass")

    # ContentsManager API part 2: methods that have useable default
    # implementations, but can be overridden in subclasses.

    def info_string(self):
        return "Serving contents"

    def get_kernel_path(self, name, path='', model=None):
        """ Return the path to start kernel in """
        return path

    def increment_filename(self, filename, path=''):
        """Increment a filename until it is unique.

        Parameters
        ----------
        filename : unicode
            The name of a file, including extension
        path : unicode
            The API path of the target's directory

        Returns
        -------
        name : unicode
            A filename that is unique, based on the input filename.
        """
        path = path.strip('/')
        basename, ext = os.path.splitext(filename)
        for i in itertools.count():
            name = u'{basename}{i}{ext}'.format(basename=basename, i=i,
                                                ext=ext)
            if not self.file_exists(name, path):
                break
        return name

    def create_file(self, model=None, path='', ext='.ipynb'):
        """Create a new file or directory and return its model with no content."""
        path = path.strip('/')
        if model is None:
            model = {}
        if 'content' not in model and model.get('type', None) != 'directory':
            if ext == '.ipynb':
                metadata = current.new_metadata(name=u'')
                model['content'] = current.new_notebook(metadata=metadata)
                model['type'] = 'notebook'
                model['format'] = 'json'
            else:
                model['content'] = ''
                model['type'] = 'file'
                model['format'] = 'text'
        if 'name' not in model:
            if model['type'] == 'directory':
                untitled = self.untitled_directory
            elif model['type'] == 'notebook':
                untitled = self.untitled_notebook
            elif model['type'] == 'file':
                untitled = self.untitled_file
            else:
                raise HTTPError(400, "Unexpected model type: %r" % model['type'])
            model['name'] = self.increment_filename(untitled + ext, path)

        model['path'] = path
        model = self.save(model, model['name'], model['path'])
        return model

    def copy(self, from_name, to_name=None, path=''):
        """Copy an existing file and return its new model.

        If to_name not specified, increment `from_name-Copy#.ext`.

        copy_from can be a full path to a file,
        or just a base name. If a base name, `path` is used.
        """
        path = path.strip('/')
        if '/' in from_name:
            from_path, from_name = from_name.rsplit('/', 1)
        else:
            from_path = path
        model = self.get_model(from_name, from_path)
        if model['type'] == 'directory':
            raise HTTPError(400, "Can't copy directories")
        if not to_name:
            base, ext = os.path.splitext(from_name)
            copy_name = u'{0}-Copy{1}'.format(base, ext)
            to_name = self.increment_filename(copy_name, path)
        model['name'] = to_name
        model['path'] = path
        model = self.save(model, to_name, path)
        return model

    def log_info(self):
        self.log.info(self.info_string())

    def trust_notebook(self, name, path=''):
        """Explicitly trust a notebook

        Parameters
        ----------
        name : string
            The filename of the notebook
        path : string
            The notebook's directory
        """
        model = self.get_model(name, path)
        nb = model['content']
        self.log.warn("Trusting notebook %s/%s", path, name)
        self.notary.mark_cells(nb, True)
        self.save(model, name, path)

    def check_and_sign(self, nb, name='', path=''):
        """Check for trusted cells, and sign the notebook.

        Called as a part of saving notebooks.

        Parameters
        ----------
        nb : dict
            The notebook object (in nbformat.current format)
        name : string
            The filename of the notebook (for logging)
        path : string
            The notebook's directory (for logging)
        """
        if self.notary.check_cells(nb):
            self.notary.sign(nb)
        else:
            self.log.warn("Saving untrusted notebook %s/%s", path, name)

    def mark_trusted_cells(self, nb, name='', path=''):
        """Mark cells as trusted if the notebook signature matches.

        Called as a part of loading notebooks.

        Parameters
        ----------
        nb : dict
            The notebook object (in nbformat.current format)
        name : string
            The filename of the notebook (for logging)
        path : string
            The notebook's directory (for logging)
        """
        trusted = self.notary.check_signature(nb)
        if not trusted:
            self.log.warn("Notebook %s/%s is not trusted", path, name)
        self.notary.mark_cells(nb, trusted)

    def should_list(self, name):
        """Should this file/directory name be displayed in a listing?"""
        return not any(fnmatch(name, glob) for glob in self.hide_globs)
