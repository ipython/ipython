"""A base class for contents managers."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from fnmatch import fnmatch
import itertools
import os

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current, sign
from IPython.utils.traitlets import Instance, Unicode, List


class ContentsManager(LoggingConfigurable):

    notary = Instance(sign.NotebookNotary)
    def _notary_default(self):
        return sign.NotebookNotary(parent=self)

    hide_globs = List(Unicode, [u'__pycache__'], config=True, help="""
        Glob patterns to hide in file and directory listings.
    """)

    # ContentsManager API part 1: methods that must be
    # implemented in subclasses.

    def path_exists(self, path):
        """Does the API-style path (directory) actually exist?

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
        exists : bool
            Whether the path is hidden.

        """
        raise NotImplementedError

    def file_exists(self, name, path=''):
        """Returns a True if the notebook exists. Else, returns False.

        Parameters
        ----------
        name : string
            The name of the notebook you are checking.
        path : string
            The relative path to the notebook (with '/' as separator)

        Returns
        -------
        bool
        """
        raise NotImplementedError('must be implemented in a subclass')

    # TODO: Remove this after we create the contents web service and directories are
    # no longer listed by the notebook web service.
    def list_dirs(self, path):
        """List the directory models for a given API style path."""
        raise NotImplementedError('must be implemented in a subclass')

    # TODO: Remove this after we create the contents web service and directories are
    # no longer listed by the notebook web service.
    def get_dir_model(self, name, path=''):
        """Get the directory model given a directory name and its API style path.

        The keys in the model should be:
        * name
        * path
        * last_modified
        * created
        * type='directory'
        """
        raise NotImplementedError('must be implemented in a subclass')

    def list_files(self, path=''):
        """Return a list of contents dicts without content.

        This returns a list of dicts

        This list of dicts should be sorted by name::

            data = sorted(data, key=lambda item: item['name'])
        """
        raise NotImplementedError('must be implemented in a subclass')

    def get_model(self, name, path='', content=True):
        """Get the notebook model with or without content."""
        raise NotImplementedError('must be implemented in a subclass')

    def save(self, model, name, path=''):
        """Save the notebook and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def update(self, model, name, path=''):
        """Update the notebook and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def delete(self, name, path=''):
        """Delete notebook by name and path."""
        raise NotImplementedError('must be implemented in a subclass')

    def create_checkpoint(self, name, path=''):
        """Create a checkpoint of the current state of a notebook

        Returns a checkpoint_id for the new checkpoint.
        """
        raise NotImplementedError("must be implemented in a subclass")

    def list_checkpoints(self, name, path=''):
        """Return a list of checkpoints for a given notebook"""
        return []

    def restore_checkpoint(self, checkpoint_id, name, path=''):
        """Restore a notebook from one of its checkpoints"""
        raise NotImplementedError("must be implemented in a subclass")

    def delete_checkpoint(self, checkpoint_id, name, path=''):
        """delete a checkpoint for a notebook"""
        raise NotImplementedError("must be implemented in a subclass")

    def info_string(self):
        return "Serving notebooks"

    # ContentsManager API part 2: methods that have useable default
    # implementations, but can be overridden in subclasses.

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
            The URL path of the notebooks directory

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

    def create_notebook(self, model=None, path=''):
        """Create a new notebook and return its model with no content."""
        path = path.strip('/')
        if model is None:
            model = {}
        if 'content' not in model:
            metadata = current.new_metadata(name=u'')
            model['content'] = current.new_notebook(metadata=metadata)
        if 'name' not in model:
            model['name'] = self.increment_filename('Untitled.ipynb', path)

        model['path'] = path
        model = self.save(model, model['name'], model['path'])
        return model

    def copy(self, from_name, to_name=None, path=''):
        """Copy an existing file and return its new model.

        If to_name not specified, increment `from_name-Copy#.ipynb`.
        """
        path = path.strip('/')
        model = self.get(from_name, path)
        if not to_name:
            base, ext = os.path.splitext(from_name)
            copy_name = u'{0}-Copy{1}'.format(base, ext)
            to_name = self.increment_filename(copy_name, path)
        model['name'] = to_name
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
        model = self.get(name, path)
        nb = model['content']
        self.log.warn("Trusting notebook %s/%s", path, name)
        self.notary.mark_cells(nb, True)
        self.save(model, name, path)

    def check_and_sign(self, nb, name, path=''):
        """Check for trusted cells, and sign the notebook.

        Called as a part of saving notebooks.

        Parameters
        ----------
        nb : dict
            The notebook structure
        name : string
            The filename of the notebook
        path : string
            The notebook's directory
        """
        if self.notary.check_cells(nb):
            self.notary.sign(nb)
        else:
            self.log.warn("Saving untrusted notebook %s/%s", path, name)

    def mark_trusted_cells(self, nb, name, path=''):
        """Mark cells as trusted if the notebook signature matches.

        Called as a part of loading notebooks.

        Parameters
        ----------
        nb : dict
            The notebook structure
        name : string
            The filename of the notebook
        path : string
            The notebook's directory
        """
        trusted = self.notary.check_signature(nb)
        if not trusted:
            self.log.warn("Notebook %s/%s is not trusted", path, name)
        self.notary.mark_cells(nb, trusted)

    def should_list(self, name):
        """Should this file/directory name be displayed in a listing?"""
        return not any(fnmatch(name, glob) for glob in self.hide_globs)
