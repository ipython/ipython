"""Tornado handlers for the notebooks web service.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import json

from tornado import web

from IPython.html.utils import url_path_join
from IPython.utils.jsonutil import date_default

from IPython.html.base.handlers import IPythonHandler, json_errors

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
        return url_path_join(self.base_project_url, 'api', 'notebooks', path, name)

    @web.authenticated
    @json_errors
    def get(self, path='', name=None):
        """
        GET with path and no notebook lists notebooks in a directory
        GET with path and notebook name 
        
        GET get checks if a notebook is not named, an returns a list of notebooks
        in the notebook path given. If a name is given, return 
        the notebook representation"""
        nbm = self.notebook_manager
        # Check to see if a notebook name was given
        if name is None:
            # List notebooks in 'path'
            notebooks = nbm.list_notebooks(path)
            self.finish(json.dumps(notebooks, default=date_default))
        else:
            # get and return notebook representation
            model = nbm.get_notebook_model(name, path)
            self.set_header(u'Last-Modified', model[u'last_modified'])
            self.finish(json.dumps(model, default=date_default))

    @web.authenticated
    @json_errors
    def patch(self, path='', name=None):
        """patch is currently used strictly for notebook renaming.
        Changes the notebook name to the name given in data."""
        nbm = self.notebook_manager
        if name is None:
            raise web.HTTPError(400, u'Notebook name missing')
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, u'JSON body missing')
        model = nbm.update_notebook_model(model, name, path)
        if model[u'name'] != name or model[u'path'] != path:
            self.set_status(301)
            location = self.notebook_location(model[u'name'], model[u'path'])
            self.set_header(u'Location', location)
        self.set_header(u'Last-Modified', model[u'last_modified'])
        self.finish(json.dumps(model, default=date_default))

    @web.authenticated
    @json_errors
    def post(self, path='', name=None):
        """Create a new notebook in the location given by 'notebook_path'."""
        nbm = self.notebook_manager
        model = self.get_json_body()
        if name is not None:
            raise web.HTTPError(400, 'No name can be provided when POSTing a new notebook.')
        model = nbm.create_notebook_model(model, path)
        location = nbm.notebook_dir + model[u'path'] + model[u'name']
        location = self.notebook_location(model[u'name'], model[u'path'])
        self.set_header(u'Location', location)
        self.set_header(u'Last-Modified', model[u'last_modified'])
        self.set_status(201)
        self.finish(json.dumps(model, default=date_default))

    @web.authenticated
    @json_errors
    def put(self, path='', name=None):
        """saves the notebook in the location given by 'notebook_path'."""
        nbm = self.notebook_manager
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, u'JSON body missing')
        nbm.save_notebook_model(model, name, path)
        self.finish(json.dumps(model, default=date_default))

    @web.authenticated
    @json_errors
    def delete(self, path='', name=None):
        """delete the notebook in the given notebook path"""
        nbm = self.notebook_manager
        nbm.delete_notebook_model(name, path)
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
        location = url_path_join(self.base_project_url, u'/api/notebooks',
            path, name, 'checkpoints', checkpoint[u'checkpoint_id'])
        self.set_header(u'Location', location)
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


_path_regex = r"(?P<path>.*)"
_checkpoint_id_regex = r"(?P<checkpoint_id>[\w-]+)"
_notebook_name_regex = r"(?P<name>[^/]+\.ipynb)"
_notebook_path_regex = "%s/%s" % (_path_regex, _notebook_name_regex)

default_handlers = [
    (r"/api/notebooks/?%s/checkpoints" % _notebook_path_regex, NotebookCheckpointsHandler),
    (r"/api/notebooks/?%s/checkpoints/%s" % (_notebook_path_regex, _checkpoint_id_regex),
        ModifyNotebookCheckpointsHandler),
    (r"/api/notebooks/?%s" % _notebook_path_regex, NotebookHandler),
    (r"/api/notebooks/?%s/?" % _path_regex, NotebookHandler),
]



