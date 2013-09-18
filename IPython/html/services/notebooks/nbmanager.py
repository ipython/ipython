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
    def _notebook_dir_changed(self, name, old, new):
        """do a bit of validation of the notebook dir"""
        if not os.path.isabs(new):
            # If we receive a non-absolute path, make it absolute.
            abs_new = os.path.abspath(new)
            self.notebook_dir = abs_new
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

    # Map notebook_ids to notebook names
    mapping = Dict()

    def load_notebook_names(self):
        """Load the notebook names into memory.

        This should be called once immediately after the notebook manager
        is created to load the existing notebooks into the mapping in
        memory.
        """
        self.list_notebooks()

    def list_notebooks(self):
        """List all notebooks.

        This returns a list of dicts, each of the form::

            dict(notebook_id=notebook,name=name)

        This list of dicts should be sorted by name::

            data = sorted(data, key=lambda item: item['name'])
        """
        raise NotImplementedError('must be implemented in a subclass')


    def new_notebook_id(self, name):
        """Generate a new notebook_id for a name and store its mapping."""
        # TODO: the following will give stable urls for notebooks, but unless
        # the notebooks are immediately redirected to their new urls when their
        # filemname changes, nasty inconsistencies result.  So for now it's
        # disabled and instead we use a random uuid4() call.  But we leave the
        # logic here so that we can later reactivate it, whhen the necessary
        # url redirection code is written.
        #notebook_id = unicode(uuid.uuid5(uuid.NAMESPACE_URL,
        #                 'file://'+self.get_path_by_name(name).encode('utf-8')))
        
        notebook_id = unicode(uuid.uuid4())
        self.mapping[notebook_id] = name
        return notebook_id

    def delete_notebook_id(self, notebook_id):
        """Delete a notebook's id in the mapping.

        This doesn't delete the actual notebook, only its entry in the mapping.
        """
        del self.mapping[notebook_id]

    def notebook_exists(self, notebook_id):
        """Does a notebook exist?"""
        return notebook_id in self.mapping

    def get_notebook(self, notebook_id, format=u'json'):
        """Get the representation of a notebook in format by notebook_id."""
        format = unicode(format)
        if format not in self.allowed_formats:
            raise web.HTTPError(415, u'Invalid notebook format: %s' % format)
        last_modified, nb = self.read_notebook_object(notebook_id)
        kwargs = {}
        if format == 'json':
            # don't split lines for sending over the wire, because it
            # should match the Python in-memory format.
            kwargs['split_lines'] = False
        data = current.writes(nb, format, **kwargs)
        name = nb.metadata.get('name','notebook')
        return last_modified, name, data

    def read_notebook_object(self, notebook_id):
        """Get the object representation of a notebook by notebook_id."""
        raise NotImplementedError('must be implemented in a subclass')

    def save_new_notebook(self, data, name=None, format=u'json'):
        """Save a new notebook and return its notebook_id.

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

        notebook_id = self.write_notebook_object(nb)
        return notebook_id

    def save_notebook(self, notebook_id, data, name=None, format=u'json'):
        """Save an existing notebook by notebook_id."""
        if format not in self.allowed_formats:
            raise web.HTTPError(415, u'Invalid notebook format: %s' % format)

        try:
            nb = current.reads(data.decode('utf-8'), format)
        except:
            raise web.HTTPError(400, u'Invalid JSON data')

        if name is not None:
            nb.metadata.name = name
        self.write_notebook_object(nb, notebook_id)

    def write_notebook_object(self, nb, notebook_id=None):
        """Write a notebook object and return its notebook_id.

        If notebook_id is None, this method should create a new notebook_id.
        If notebook_id is not None, this method should check to make sure it
        exists and is valid.
        """
        raise NotImplementedError('must be implemented in a subclass')

    def delete_notebook(self, notebook_id):
        """Delete notebook by notebook_id."""
        raise NotImplementedError('must be implemented in a subclass')

    def increment_filename(self, name):
        """Increment a filename to make it unique.

        This exists for notebook stores that must have unique names. When a notebook
        is created or copied this method constructs a unique filename, typically
        by appending an integer to the name.
        """
        return name

    def new_notebook(self):
        """Create a new notebook and return its notebook_id."""
        name = self.increment_filename('Untitled')
        metadata = current.new_metadata(name=name)
        nb = current.new_notebook(metadata=metadata)
        notebook_id = self.write_notebook_object(nb)
        return notebook_id

    def copy_notebook(self, notebook_id):
        """Copy an existing notebook and return its notebook_id."""
        last_mod, nb = self.read_notebook_object(notebook_id)
        name = nb.metadata.name + '-Copy'
        name = self.increment_filename(name)
        nb.metadata.name = name
        notebook_id = self.write_notebook_object(nb)
        return notebook_id
    
    # Checkpoint-related
    
    def create_checkpoint(self, notebook_id):
        """Create a checkpoint of the current state of a notebook
        
        Returns a checkpoint_id for the new checkpoint.
        """
        raise NotImplementedError("must be implemented in a subclass")
    
    def list_checkpoints(self, notebook_id):
        """Return a list of checkpoints for a given notebook"""
        return []
    
    def restore_checkpoint(self, notebook_id, checkpoint_id):
        """Restore a notebook from one of its checkpoints"""
        raise NotImplementedError("must be implemented in a subclass")

    def delete_checkpoint(self, notebook_id, checkpoint_id):
        """delete a checkpoint for a notebook"""
        raise NotImplementedError("must be implemented in a subclass")
    
    def log_info(self):
        self.log.info(self.info_string())
    
    def info_string(self):
        return "Serving notebooks"

