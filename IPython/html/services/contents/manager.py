"""A base class for contents managers."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from fnmatch import fnmatch
import itertools
import json
import os
import re

from tornado.web import HTTPError

from .checkpoints import Checkpoints
from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import sign, validate, ValidationError
from IPython.nbformat.v4 import new_notebook
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import (
    Any,
    Dict,
    Instance,
    List,
    TraitError,
    Type,
    Unicode,
)
from IPython.utils.py3compat import string_types

copy_pat = re.compile(r'\-Copy\d*\.')


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

    pre_save_hook = Any(None, config=True,
        help="""Python callable or importstring thereof

        To be called on a contents model prior to save.

        This can be used to process the structure,
        such as removing notebook outputs or other side effects that
        should not be saved.

        It will be called as (all arguments passed by keyword)::

            hook(path=path, model=model, contents_manager=self)

        - model: the model to be saved. Includes file contents.
          Modifying this dict will affect the file that is stored.
        - path: the API path of the save destination
        - contents_manager: this ContentsManager instance
        """
    )
    def _pre_save_hook_changed(self, name, old, new):
        if new and isinstance(new, string_types):
            self.pre_save_hook = import_item(self.pre_save_hook)
        elif new:
            if not callable(new):
                raise TraitError("pre_save_hook must be callable")

    def run_pre_save_hook(self, model, path, **kwargs):
        """Run the pre-save hook if defined, and log errors"""
        if self.pre_save_hook:
            try:
                self.log.debug("Running pre-save hook on %s", path)
                self.pre_save_hook(model=model, path=path, contents_manager=self, **kwargs)
            except Exception:
                self.log.error("Pre-save hook failed on %s", path, exc_info=True)

    checkpoints_class = Type(Checkpoints, config=True)
    checkpoints = Instance(Checkpoints, config=True)
    checkpoints_kwargs = Dict(allow_none=False, config=True)

    def _checkpoints_default(self):
        return self.checkpoints_class(**self.checkpoints_kwargs)

    def _checkpoints_kwargs_default(self):
        return dict(
            parent=self,
            log=self.log,
        )

    # ContentsManager API part 1: methods that must be
    # implemented in subclasses.

    def dir_exists(self, path):
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

    def file_exists(self, path=''):
        """Does a file exist at the given path?

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

    def exists(self, path):
        """Does a file or directory exist at the given path?

        Like os.path.exists

        Parameters
        ----------
        path : string
            The relative path to the file's directory (with '/' as separator)

        Returns
        -------
        exists : bool
            Whether the target exists.
        """
        return self.file_exists(path) or self.dir_exists(path)

    def get(self, path, content=True, type=None, format=None):
        """Get the model of a file or directory with or without content."""
        raise NotImplementedError('must be implemented in a subclass')

    def save(self, model, path):
        """Save the file or directory and return the model with no content.

        Save implementations should call self.run_pre_save_hook(model=model, path=path)
        prior to writing any data.
        """
        raise NotImplementedError('must be implemented in a subclass')

    def delete_file(self, path):
        """Delete file or directory by path."""
        raise NotImplementedError('must be implemented in a subclass')

    def rename_file(self, old_path, new_path):
        """Rename a file."""
        raise NotImplementedError('must be implemented in a subclass')

    # ContentsManager API part 2: methods that have useable default
    # implementations, but can be overridden in subclasses.

    def delete(self, path):
        """Delete a file/directory and any associated checkpoints."""
        path = path.strip('/')
        if not path:
            raise HTTPError(400, "Can't delete root")
        self.delete_file(path)
        self.checkpoints.delete_all_checkpoints(path)

    def rename(self, old_path, new_path):
        """Rename a file and any checkpoints associated with that file."""
        self.rename_file(old_path, new_path)
        self.checkpoints.rename_all_checkpoints(old_path, new_path)

    def update(self, model, path):
        """Update the file's path

        For use in PATCH requests, to enable renaming a file without
        re-uploading its contents. Only used for renaming at the moment.
        """
        path = path.strip('/')
        new_path = model.get('path', path).strip('/')
        if path != new_path:
            self.rename(path, new_path)
        model = self.get(new_path, content=False)
        return model

    def info_string(self):
        return "Serving contents"

    def get_kernel_path(self, path, model=None):
        """Return the API path for the kernel
        
        KernelManagers can turn this value into a filesystem path,
        or ignore it altogether.

        The default value here will start kernels in the directory of the
        notebook server. FileContentsManager overrides this to use the
        directory containing the notebook.
        """
        return ''

    def increment_filename(self, filename, path='', insert=''):
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
            if i:
                insert_i = '{}{}'.format(insert, i)
            else:
                insert_i = ''
            name = u'{basename}{insert}{ext}'.format(basename=basename,
                insert=insert_i, ext=ext)
            if not self.exists(u'{}/{}'.format(path, name)):
                break
        return name

    def validate_notebook_model(self, model):
        """Add failed-validation message to model"""
        try:
            validate(model['content'])
        except ValidationError as e:
            model['message'] = u'Notebook Validation failed: {}:\n{}'.format(
                e.message, json.dumps(e.instance, indent=1, default=lambda obj: '<UNKNOWN>'),
            )
        return model
    
    def new_untitled(self, path='', type='', ext=''):
        """Create a new untitled file or directory in path
        
        path must be a directory
        
        File extension can be specified.
        
        Use `new` to create files with a fully specified path (including filename).
        """
        path = path.strip('/')
        if not self.dir_exists(path):
            raise HTTPError(404, 'No such directory: %s' % path)
        
        model = {}
        if type:
            model['type'] = type
        
        if ext == '.ipynb':
            model.setdefault('type', 'notebook')
        else:
            model.setdefault('type', 'file')
        
        insert = ''
        if model['type'] == 'directory':
            untitled = self.untitled_directory
            insert = ' '
        elif model['type'] == 'notebook':
            untitled = self.untitled_notebook
            ext = '.ipynb'
        elif model['type'] == 'file':
            untitled = self.untitled_file
        else:
            raise HTTPError(400, "Unexpected model type: %r" % model['type'])
        
        name = self.increment_filename(untitled + ext, path, insert=insert)
        path = u'{0}/{1}'.format(path, name)
        return self.new(model, path)
    
    def new(self, model=None, path=''):
        """Create a new file or directory and return its model with no content.
        
        To create a new untitled entity in a directory, use `new_untitled`.
        """
        path = path.strip('/')
        if model is None:
            model = {}
        
        if path.endswith('.ipynb'):
            model.setdefault('type', 'notebook')
        else:
            model.setdefault('type', 'file')
        
        # no content, not a directory, so fill out new-file model
        if 'content' not in model and model['type'] != 'directory':
            if model['type'] == 'notebook':
                model['content'] = new_notebook()
                model['format'] = 'json'
            else:
                model['content'] = ''
                model['type'] = 'file'
                model['format'] = 'text'
        
        model = self.save(model, path)
        return model

    def copy(self, from_path, to_path=None):
        """Copy an existing file and return its new model.

        If to_path not specified, it will be the parent directory of from_path.
        If to_path is a directory, filename will increment `from_path-Copy#.ext`.

        from_path must be a full path to a file.
        """
        path = from_path.strip('/')
        if to_path is not None:
            to_path = to_path.strip('/')

        if '/' in path:
            from_dir, from_name = path.rsplit('/', 1)
        else:
            from_dir = ''
            from_name = path
        
        model = self.get(path)
        model.pop('path', None)
        model.pop('name', None)
        if model['type'] == 'directory':
            raise HTTPError(400, "Can't copy directories")
        
        if to_path is None:
            to_path = from_dir
        if self.dir_exists(to_path):
            name = copy_pat.sub(u'.', from_name)
            to_name = self.increment_filename(name, to_path, insert='-Copy')
            to_path = u'{0}/{1}'.format(to_path, to_name)
        
        model = self.save(model, to_path)
        return model

    def log_info(self):
        self.log.info(self.info_string())

    def trust_notebook(self, path):
        """Explicitly trust a notebook

        Parameters
        ----------
        path : string
            The path of a notebook
        """
        model = self.get(path)
        nb = model['content']
        self.log.warn("Trusting notebook %s", path)
        self.notary.mark_cells(nb, True)
        self.save(model, path)

    def check_and_sign(self, nb, path=''):
        """Check for trusted cells, and sign the notebook.

        Called as a part of saving notebooks.

        Parameters
        ----------
        nb : dict
            The notebook dict
        path : string
            The notebook's path (for logging)
        """
        if self.notary.check_cells(nb):
            self.notary.sign(nb)
        else:
            self.log.warn("Saving untrusted notebook %s", path)

    def mark_trusted_cells(self, nb, path=''):
        """Mark cells as trusted if the notebook signature matches.

        Called as a part of loading notebooks.

        Parameters
        ----------
        nb : dict
            The notebook object (in current nbformat)
        path : string
            The notebook's path (for logging)
        """
        trusted = self.notary.check_signature(nb)
        if not trusted:
            self.log.warn("Notebook %s is not trusted", path)
        self.notary.mark_cells(nb, trusted)

    def should_list(self, name):
        """Should this file/directory name be displayed in a listing?"""
        return not any(fnmatch(name, glob) for glob in self.hide_globs)

    # Part 3: Checkpoints API
    def create_checkpoint(self, path):
        """Create a checkpoint."""
        return self.checkpoints.create_checkpoint(self, path)

    def restore_checkpoint(self, checkpoint_id, path):
        """
        Restore a checkpoint.
        """
        self.checkpoints.restore_checkpoint(self, checkpoint_id, path)

    def list_checkpoints(self, path):
        return self.checkpoints.list_checkpoints(path)

    def delete_checkpoint(self, checkpoint_id, path):
        return self.checkpoints.delete_checkpoint(checkpoint_id, path)
