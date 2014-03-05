"""A base class notebook manager.

Authors:

* Brian Granger
* Zach Sailer
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from fnmatch import fnmatch
import itertools
import os

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current, sign
from IPython.utils.traitlets import Instance, Unicode, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class NotebookManager(LoggingConfigurable):

    filename_ext = Unicode(u'.ipynb')
    
    notary = Instance(sign.NotebookNotary)
    def _notary_default(self):
        return sign.NotebookNotary(parent=self)
    
    hide_globs = List(Unicode, [u'__pycache__'], config=True, help="""
        Glob patterns to hide in file and directory listings.
    """)

    # NotebookManager API part 1: methods that must be
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
            relative to base notebook-dir).
        
        Returns
        -------
        exists : bool
            Whether the path is hidden.
        
        """
        raise NotImplementedError

    def notebook_exists(self, name, path=''):
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

    def list_notebooks(self, path=''):
        """Return a list of notebook dicts without content.

        This returns a list of dicts, each of the form::

            dict(notebook_id=notebook,name=name)

        This list of dicts should be sorted by name::

            data = sorted(data, key=lambda item: item['name'])
        """
        raise NotImplementedError('must be implemented in a subclass')

    def get_notebook(self, name, path='', content=True):
        """Get the notebook model with or without content."""
        raise NotImplementedError('must be implemented in a subclass')

    def save_notebook(self, model, name, path=''):
        """Save the notebook and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def update_notebook(self, model, name, path=''):
        """Update the notebook and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def delete_notebook(self, name, path=''):
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

    # NotebookManager API part 2: methods that have useable default
    # implementations, but can be overridden in subclasses.

    def increment_filename(self, basename, path=''):
        """Increment a notebook filename without the .ipynb to make it unique.
        
        Parameters
        ----------
        basename : unicode
            The name of a notebook without the ``.ipynb`` file extension.
        path : unicode
            The URL path of the notebooks directory

        Returns
        -------
        name : unicode
            A notebook name (with the .ipynb extension) that starts
            with basename and does not refer to any existing notebook.
        """
        path = path.strip('/')
        for i in itertools.count():
            name = u'{basename}{i}{ext}'.format(basename=basename, i=i,
                                                ext=self.filename_ext)
            if not self.notebook_exists(name, path):
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
            model['name'] = self.increment_filename('Untitled', path)
            
        model['path'] = path
        model = self.save_notebook(model, model['name'], model['path'])
        return model

    def copy_notebook(self, from_name, to_name=None, path=''):
        """Copy an existing notebook and return its new model.
        
        If to_name not specified, increment `from_name-Copy#.ipynb`.
        """
        path = path.strip('/')
        model = self.get_notebook(from_name, path)
        if not to_name:
            base = os.path.splitext(from_name)[0] + '-Copy'
            to_name = self.increment_filename(base, path)
        model['name'] = to_name
        model = self.save_notebook(model, to_name, path)
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
        model = self.get_notebook(name, path)
        nb = model['content']
        self.log.warn("Trusting notebook %s/%s", path, name)
        self.notary.mark_cells(nb, True)
        self.save_notebook(model, name, path)
    
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
