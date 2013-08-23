"""A base class notebook manager.

Authors:

* Brian Granger
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
import uuid

from tornado import web
from urllib import quote, unquote

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current
from IPython.utils.traitlets import List, Dict, Unicode, TraitError

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
    notebook_dir = Unicode(os.getcwdu(), config=True, help="""
            The directory to use for notebooks.
            """)

    def named_notebook_path(self, notebook_path):
        """Given a notebook_path name, returns a (name, path) tuple, where
        name is a .ipynb file, and path is the directory for the file, which
        *always* starts *and* ends with a '/' character.

        Parameters
        ----------
        notebook_path : string
            A path that may be a .ipynb name or a directory

        Returns
        -------
        name : string or None
            the filename of the notebook, or None if not a .ipynb extension
        path : string
            the path to the directory which contains the notebook
        """
        names = notebook_path.split('/')
        names = [n for n in names if n != ''] # remove duplicate splits

        names = [''] + names

        if names and names[-1].endswith(".ipynb"):
            name = names[-1]
            path = "/".join(names[:-1]) + '/'
        else:
            name = None
            path = "/".join(names) + '/'
        return name, path
        
    def get_os_path(self, fname=None, path='/'):
        """Given a notebook name and a server URL path, return its file system
        path.

        Parameters
        ----------
        fname : string
            The name of a notebook file with the .ipynb extension
        path : string
            The relative URL path (with '/' as separator) to the named
            notebook.

        Returns
        -------
        path : string
            A file system path that combines notebook_dir (location where
            server started), the relative path, and the filename with the
            current operating system's url.
        """
        parts = path.split('/')
        parts = [p for p in parts if p != ''] # remove duplicate splits
        if fname is not None:
            parts += [fname]
        path = os.path.join(self.notebook_dir, *parts)
        return path

    def url_encode(self, path):
        """Returns the path with all special characters URL encoded"""
        parts = os.path.split(path)
        return os.path.join(*[quote(p) for p in parts])

    def url_decode(self, path):
        """Returns the URL with special characters decoded"""
        parts = os.path.split(path)
        return os.path.join(*[unquote(p) for p in parts])

    def _notebook_dir_changed(self, new):
        """do a bit of validation of the notebook dir"""
        if not os.path.isabs(new):
            # If we receive a non-absolute path, make it absolute.
            abs_new = os.path.abspath(new)
            #self.notebook_dir = os.path.dirname(abs_new)
            return
        if os.path.exists(new) and not os.path.isdir(new):
            raise TraitError("notebook dir %r is not a directory" % new)
        if not os.path.exists(new):
            self.log.info("Creating notebook dir %s", new)
            try:
                os.mkdir(new)
            except:
                raise TraitError("Couldn't create notebook dir %r" % new)
                
    allowed_formats = List([u'json',u'py'])

    def add_new_folder(self, path=None):
        new_path = os.path.join(self.notebook_dir, path)
        if not os.path.exists(new_path):
            os.makedirs(new_path) 
        else:
            raise web.HTTPError(409, u'Directory already exists or creation permission not allowed.')

    def load_notebook_names(self, path):
        """Load the notebook names into memory.

        This should be called once immediately after the notebook manager
        is created to load the existing notebooks into the mapping in
        memory.
        """
        self.list_notebooks(path)

    def list_notebooks(self):
        """List all notebooks.

        This returns a list of dicts, each of the form::

            dict(notebook_id=notebook,name=name)

        This list of dicts should be sorted by name::

            data = sorted(data, key=lambda item: item['name'])
        """
        raise NotImplementedError('must be implemented in a subclass')

    def notebook_model(self, name, path='/', content=True):
        """ Creates the standard notebook model """
        last_modified, contents = self.read_notebook_model(name, path)
        model = {"name": name, 
                    "path": path,
                    "last_modified": last_modified.ctime()}
        if content is True:
            model['content'] = contents
        return model

    def get_notebook(self, notebook_name, notebook_path='/', format=u'json'):
        """Get the representation of a notebook in format by notebook_name."""
        format = unicode(format)
        if format not in self.allowed_formats:
            raise web.HTTPError(415, u'Invalid notebook format: %s' % format)
        kwargs = {}
        last_mod, nb = self.read_notebook_object(notebook_name, notebook_path)
        if format == 'json':
            # don't split lines for sending over the wire, because it
            # should match the Python in-memory format.
            kwargs['split_lines'] = False
        representation = current.writes(nb, format, **kwargs)
        name = nb.metadata.get('name', 'notebook')
        return last_mod, representation, name

    def read_notebook_model(self, notebook_name, notebook_path='/'):
        """Get the object representation of a notebook by notebook_id."""
        raise NotImplementedError('must be implemented in a subclass')

    def save_notebook(self, model, name=None, path='/'):
        """Save the Notebook"""
        if name is None:
            name = self.increment_filename('Untitled', path)
        if 'content' not in model:
            metadata = current.new_metadata(name=name)
            nb = current.new_notebook(metadata=metadata)
        else:
            nb = model['content']
        self.write_notebook_object()
            

    def save_new_notebook(self, data, notebook_path='/', name=None, format=u'json'):
        """Save a new notebook and return its name.

        If a name is passed in, it overrides any values in the notebook data
        and the value in the data is updated to use that value.
        """
        if format not in self.allowed_formats:
            raise web.HTTPError(415, u'Invalid notebook format: %s' % format)

        try:
            nb = current.reads(data.decode('utf-8'), format)
        except:
            raise web.HTTPError(400, u'Invalid JSON data')

        if name is None:
           try:
               name = nb.metadata.name
           except AttributeError:
               raise web.HTTPError(400, u'Missing notebook name')
        nb.metadata.name = name

        notebook_name = self.write_notebook_object(nb, notebook_path=notebook_path)
        return notebook_name

    def save_notebook(self, data, notebook_path='/', name=None, format=u'json'):
        """Save an existing notebook by notebook_name."""
        if format not in self.allowed_formats:
            raise web.HTTPError(415, u'Invalid notebook format: %s' % format)

        try:
            nb = current.reads(data.decode('utf-8'), format)
        except:
            raise web.HTTPError(400, u'Invalid JSON data')

        if name is not None:
            nb.metadata.name = name
        self.write_notebook_object(nb, name, notebook_path, new_name)

    def write_notebook_model(self, model):
        """Write a notebook object and return its notebook_name.

        If notebook_name is None, this method should create a new notebook_name.
        If notebook_name is not None, this method should check to make sure it
        exists and is valid.
        """
        raise NotImplementedError('must be implemented in a subclass')

    def delete_notebook(self, notebook_name, notebook_path):
        """Delete notebook by notebook_id."""
        raise NotImplementedError('must be implemented in a subclass')

    def increment_filename(self, name):
        """Increment a filename to make it unique.

        This exists for notebook stores that must have unique names. When a notebook
        is created or copied this method constructs a unique filename, typically
        by appending an integer to the name.
        """
        return name

    def new_notebook(self, notebook_path='/'):
        """Create a new notebook and return its notebook_name."""
        name = self.increment_filename('Untitled', notebook_path)
        metadata = current.new_metadata(name=name)
        nb = current.new_notebook(metadata=metadata)
        notebook_name = self.write_notebook_object(nb, notebook_path=notebook_path)
        return notebook_name

    def copy_notebook(self, name, path='/'):
        """Copy an existing notebook and return its new notebook_name."""
        last_mod, nb = self.read_notebook_object(name, path)
        name = nb.metadata.name + '-Copy'
        name = self.increment_filename(name, path)
        nb.metadata.name = name
        notebook_name = self.write_notebook_object(nb, notebook_path = path)
        return notebook_name  
    
    # Checkpoint-related
    
    def create_checkpoint(self, notebook_name, notebook_path='/'):
        """Create a checkpoint of the current state of a notebook
        
        Returns a checkpoint_id for the new checkpoint.
        """
        raise NotImplementedError("must be implemented in a subclass")
    
    def list_checkpoints(self, notebook_name, notebook_path='/'):
        """Return a list of checkpoints for a given notebook"""
        return []
    
    def restore_checkpoint(self, notebook_name, checkpoint_id, notebook_path='/'):
        """Restore a notebook from one of its checkpoints"""
        raise NotImplementedError("must be implemented in a subclass")

    def delete_checkpoint(self, notebook_name, checkpoint_id, notebook_path='/'):
        """delete a checkpoint for a notebook"""
        raise NotImplementedError("must be implemented in a subclass")
    
    def log_info(self):
        self.log.info(self.info_string())
    
    def info_string(self):
        return "Serving notebooks"
