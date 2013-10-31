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

import os

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current
from IPython.utils import py3compat
from IPython.utils.traitlets import Unicode, TraitError

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class NotebookManager(LoggingConfigurable):

    # Todo:
    # The notebook_dir attribute is used to mean a couple of different things:
    # 1. Where the notebooks are stored if FileNotebookManager is used.
    # 2. The cwd of the kernel for a project.
    # Right now we use this attribute in a number of different places and
    # we are going to have to disentangle all of this.
    notebook_dir = Unicode(py3compat.getcwd(), config=True, help="""
            The directory to use for notebooks.
            """)

    filename_ext = Unicode(u'.ipynb')
    
    def path_exists(self, path):
        """Does the API-style path (directory) actually exist?
        
        Override this method in subclasses.
        
        Parameters
        ----------
        path : string
            The 
        
        Returns
        -------
        exists : bool
            Whether the path does indeed exist.
        """
        raise NotImplementedError
    
    def _notebook_dir_changed(self, name, old, new):
        """Do a bit of validation of the notebook dir."""
        if not os.path.isabs(new):
            # If we receive a non-absolute path, make it absolute.
            self.notebook_dir = os.path.abspath(new)
            return
        if os.path.exists(new) and not os.path.isdir(new):
            raise TraitError("notebook dir %r is not a directory" % new)
        if not os.path.exists(new):
            self.log.info("Creating notebook dir %s", new)
            try:
                os.mkdir(new)
            except:
                raise TraitError("Couldn't create notebook dir %r" % new)

    # Main notebook API

    def increment_filename(self, basename, path=''):
        """Increment a notebook filename without the .ipynb to make it unique.
        
        Parameters
        ----------
        basename : unicode
            The name of a notebook without the ``.ipynb`` file extension.
        path : unicode
            The URL path of the notebooks directory
        """
        return basename

    def list_notebooks(self, path=''):
        """Return a list of notebook dicts without content.

        This returns a list of dicts, each of the form::

            dict(notebook_id=notebook,name=name)

        This list of dicts should be sorted by name::

            data = sorted(data, key=lambda item: item['name'])
        """
        raise NotImplementedError('must be implemented in a subclass')

    def get_notebook_model(self, name, path='', content=True):
        """Get the notebook model with or without content."""
        raise NotImplementedError('must be implemented in a subclass')

    def save_notebook_model(self, model, name, path=''):
        """Save the notebook model and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def update_notebook_model(self, model, name, path=''):
        """Update the notebook model and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def delete_notebook_model(self, name, path=''):
        """Delete notebook by name and path."""
        raise NotImplementedError('must be implemented in a subclass')

    def create_notebook_model(self, model=None, path=''):
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
        model = self.save_notebook_model(model, model['name'], model['path'])
        return model

    def copy_notebook(self, from_name, to_name=None, path=''):
        """Copy an existing notebook and return its new model.
        
        If to_name not specified, increment `from_name-Copy#.ipynb`.
        """
        path = path.strip('/')
        model = self.get_notebook_model(from_name, path)
        if not to_name:
            base = os.path.splitext(from_name)[0] + '-Copy'
            to_name = self.increment_filename(base, path)
        model['name'] = to_name
        model = self.save_notebook_model(model, to_name, path)
        return model
    
    # Checkpoint-related
    
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
    
    def log_info(self):
        self.log.info(self.info_string())
    
    def info_string(self):
        return "Serving notebooks"
