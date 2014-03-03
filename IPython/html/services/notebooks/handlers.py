"""Tornado handlers for the notebooks web service.

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

import json

from tornado import web

from IPython.html.utils import url_path_join, url_escape
from IPython.utils.jsonutil import date_default

from IPython.html.base.handlers import (IPythonHandler, json_errors,
                                    notebook_path_regex, path_regex,
                                    notebook_name_regex)

#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------


class NotebookHandler(IPythonHandler):

    SUPPORTED_METHODS = (u'GET', u'PUT', u'PATCH', u'POST', u'DELETE')

    def notebook_location(self, name, path=''):
        """Return the full URL location of a notebook based.
        
        Parameters
        ----------
        name : unicode
            The base name of the notebook, such as "foo.ipynb".
        path : unicode
            The URL path of the notebook.
        """
        return url_escape(url_path_join(
            self.base_url, 'api', 'notebooks', path, name
        ))

    def _finish_model(self, model, location=True):
        """Finish a JSON request with a model, setting relevant headers, etc."""
        if location:
            location = self.notebook_location(model['name'], model['path'])
            self.set_header('Location', location)
        self.set_header('Last-Modified', model['last_modified'])
        self.finish(json.dumps(model, default=date_default))
    
    @web.authenticated
    @json_errors
    def get(self, path='', name=None):
        """Return a Notebook or list of notebooks.

        * GET with path and no notebook name lists notebooks in a directory
        * GET with path and notebook name returns notebook JSON
        """
        nbm = self.notebook_manager
        # Check to see if a notebook name was given
        if name is None:
            # TODO: Remove this after we create the contents web service and directories are
            # no longer listed by the notebook web service. This should only handle notebooks
            # and not directories.
            dirs = nbm.list_dirs(path)
            notebooks = []
            index = []
            for nb in nbm.list_notebooks(path):
                if nb['name'].lower() == 'index.ipynb':
                    index.append(nb)
                else:
                    notebooks.append(nb)
            notebooks = index + dirs + notebooks
            self.finish(json.dumps(notebooks, default=date_default))
            return
        # get and return notebook representation
        model = nbm.get_notebook(name, path)
        self._finish_model(model, location=False)

    @web.authenticated
    @json_errors
    def patch(self, path='', name=None):
        """PATCH renames a notebook without re-uploading content."""
        nbm = self.notebook_manager
        if name is None:
            raise web.HTTPError(400, u'Notebook name missing')
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, u'JSON body missing')
        model = nbm.update_notebook(model, name, path)
        self._finish_model(model)
    
    def _copy_notebook(self, copy_from, path, copy_to=None):
        """Copy a notebook in path, optionally specifying the new name.
        
        Only support copying within the same directory.
        """
        self.log.info(u"Copying notebook from %s/%s to %s/%s",
            path, copy_from,
            path, copy_to or '',
        )
        model = self.notebook_manager.copy_notebook(copy_from, copy_to, path)
        self.set_status(201)
        self._finish_model(model)
    
    def _upload_notebook(self, model, path, name=None):
        """Upload a notebook
        
        If name specified, create it in path/name.
        """
        self.log.info(u"Uploading notebook to %s/%s", path, name or '')
        if name:
            model['name'] = name
        
        model = self.notebook_manager.create_notebook(model, path)
        self.set_status(201)
        self._finish_model(model)
    
    def _create_empty_notebook(self, path, name=None):
        """Create an empty notebook in path
        
        If name specified, create it in path/name.
        """
        self.log.info(u"Creating new notebook in %s/%s", path, name or '')
        model = {}
        if name:
            model['name'] = name
        model = self.notebook_manager.create_notebook(model, path=path)
        self.set_status(201)
        self._finish_model(model)
    
    def _save_notebook(self, model, path, name):
        """Save an existing notebook."""
        self.log.info(u"Saving notebook at %s/%s", path, name)
        model = self.notebook_manager.save_notebook(model, name, path)
        if model['path'] != path.strip('/') or model['name'] != name:
            # a rename happened, set Location header
            location = True
        else:
            location = False
        self._finish_model(model, location)
    
    @web.authenticated
    @json_errors
    def post(self, path='', name=None):
        """Create a new notebook in the specified path.
        
        POST creates new notebooks. The server always decides on the notebook name.
        
        POST /api/notebooks/path
          New untitled notebook in path. If content specified, upload a
          notebook, otherwise start empty.
        POST /api/notebooks/path?copy=OtherNotebook.ipynb
          New copy of OtherNotebook in path
        """
        
        if name is not None:
            raise web.HTTPError(400, "Only POST to directories. Use PUT for full names.")
        
        model = self.get_json_body()
        
        if model is not None:
            copy_from = model.get('copy_from')
            if copy_from:
                if model.get('content'):
                    raise web.HTTPError(400, "Can't upload and copy at the same time.")
                self._copy_notebook(copy_from, path)
            else:
                self._upload_notebook(model, path)
        else:
            self._create_empty_notebook(path)

    @web.authenticated
    @json_errors
    def put(self, path='', name=None):
        """Saves the notebook in the location specified by name and path.
        
        PUT is very similar to POST, but the requester specifies the name,
        whereas with POST, the server picks the name.
        
        PUT /api/notebooks/path/Name.ipynb
          Save notebook at ``path/Name.ipynb``. Notebook structure is specified
          in `content` key of JSON request body. If content is not specified,
          create a new empty notebook.
        PUT /api/notebooks/path/Name.ipynb?copy=OtherNotebook.ipynb
          Copy OtherNotebook to Name
        """
        if name is None:
            raise web.HTTPError(400, "Only PUT to full names. Use POST for directories.")
        
        model = self.get_json_body()
        if model:
            copy_from = model.get('copy_from')
            if copy_from:
                if model.get('content'):
                    raise web.HTTPError(400, "Can't upload and copy at the same time.")
                self._copy_notebook(copy_from, path, name)
            elif self.notebook_manager.notebook_exists(name, path):
                self._save_notebook(model, path, name)
            else:
                self._upload_notebook(model, path, name)
        else:
            self._create_empty_notebook(path, name)

    @web.authenticated
    @json_errors
    def delete(self, path='', name=None):
        """delete the notebook in the given notebook path"""
        nbm = self.notebook_manager
        nbm.delete_notebook(name, path)
        self.set_status(204)
        self.finish()


class NotebookCheckpointsHandler(IPythonHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST')
    
    @web.authenticated
    @json_errors
    def get(self, path='', name=None):
        """get lists checkpoints for a notebook"""
        nbm = self.notebook_manager
        checkpoints = nbm.list_checkpoints(name, path)
        data = json.dumps(checkpoints, default=date_default)
        self.finish(data)
    
    @web.authenticated
    @json_errors
    def post(self, path='', name=None):
        """post creates a new checkpoint"""
        nbm = self.notebook_manager
        checkpoint = nbm.create_checkpoint(name, path)
        data = json.dumps(checkpoint, default=date_default)
        location = url_path_join(self.base_url, 'api/notebooks',
            path, name, 'checkpoints', checkpoint['id'])
        self.set_header('Location', url_escape(location))
        self.set_status(201)
        self.finish(data)


class ModifyNotebookCheckpointsHandler(IPythonHandler):
    
    SUPPORTED_METHODS = ('POST', 'DELETE')
    
    @web.authenticated
    @json_errors
    def post(self, path, name, checkpoint_id):
        """post restores a notebook from a checkpoint"""
        nbm = self.notebook_manager
        nbm.restore_checkpoint(checkpoint_id, name, path)
        self.set_status(204)
        self.finish()
    
    @web.authenticated
    @json_errors
    def delete(self, path, name, checkpoint_id):
        """delete clears a checkpoint for a given notebook"""
        nbm = self.notebook_manager
        nbm.delete_checkpoint(checkpoint_id, name, path)
        self.set_status(204)
        self.finish()
        
#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_checkpoint_id_regex = r"(?P<checkpoint_id>[\w-]+)"

default_handlers = [
    (r"/api/notebooks%s/checkpoints" % notebook_path_regex, NotebookCheckpointsHandler),
    (r"/api/notebooks%s/checkpoints/%s" % (notebook_path_regex, _checkpoint_id_regex),
        ModifyNotebookCheckpointsHandler),
    (r"/api/notebooks%s" % notebook_path_regex, NotebookHandler),
    (r"/api/notebooks%s" % path_regex, NotebookHandler),
]

