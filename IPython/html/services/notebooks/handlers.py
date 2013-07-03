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

from tornado import web

from zmq.utils import jsonapi

from IPython.utils.jsonutil import date_default

from ...base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------


class NotebookRootHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        nbm = self.notebook_manager
        km = self.kernel_manager
        notebook_names = nbm.list_notebooks("")
        notebooks = []
        for name in notebook_names:
            model = nbm.notebook_model(name)
            notebooks.append(model)
        self.finish(jsonapi.dumps(notebooks))

    @web.authenticated
    def post(self):
        nbm = self.notebook_manager
        notebook_name = nbm.new_notebook()
        model = nbm.notebook_model(notebook_name)
        self.set_header('Location', '{0}api/notebooks/{1}'.format(self.base_project_url, notebook_name))
        self.finish(jsonapi.dumps(model))
        
        
class NotebookRootRedirect(IPythonHandler):

    @authenticate_unless_readonly
    def get(self):
        self.redirect("/api/notebooks")


class NotebookHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    @web.authenticated
    def get(self, notebook_path):
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        
        if name == None:
            notebook_names = nbm.list_notebooks(path)
            notebooks = []
            for name in notebook_names:
                model = nbm.notebook_model(name,path)
                notebooks.append(model)
            self.finish(jsonapi.dumps(notebooks))
        else:
            format = self.get_argument('format', default='json')
            model = nbm.notebook_model(name,path)
            data, name = nbm.get_notebook(model, format)

            if format == u'json':
                self.set_header('Content-Type', 'application/json')
                self.set_header('Content-Disposition','attachment; filename="%s.ipynb"' % name)
            elif format == u'py':
                self.set_header('Content-Type', 'application/x-python')
                self.set_header('Content-Disposition','attachment; filename="%s.py"' % name)
            #self.set_header('Last-Modified', last_mod)
            self.finish(jsonapi.dumps(model))

    @web.authenticated
    def put(self, notebook_path):
        nbm = self.notebook_manager
        notebook_name, notebook_path = nbm.named_notebook_path(notebook_path)        
        if notebook_name == None:
            body = self.request.body.strip()
            format = self.get_argument('format', default='json')
            name = self.get_argument('name', default=None)
            if body:
                notebook_name = nbm.save_new_notebook(body, notebook_path=notebook_path, name=name, format=format)
            else:
                notebook_name = nbm.new_notebook(notebook_path=notebook_path)
            if notebook_path==None:
                self.set_header('Location', nbm.notebook_dir + '/'+ notebook_name)
            else:
                self.set_header('Location', nbm.notebook_dir + '/'+ notebook_path + '/' + notebook_name)
            model = nbm.notebook_model(notebook_name, notebook_path)
            self.finish(jsonapi.dumps(model))
        else:            
            format = self.get_argument('format', default='json')
            name = self.get_argument('name', default=None)
            nbm.save_notebook(self.request.body, notebook_path=notebook_path, name=name, format=format)
            model = nbm.notebook_model(notebook_name, notebook_path)
            self.set_status(204)
            self.finish(jsonapi.dumps(model))

    @web.authenticated
    def delete(self, notebook_path):
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        nbm.delete_notebook(name, path)
        self.set_status(204)
        self.finish()


class NotebookCheckpointsHandler(IPythonHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST')
    
    @web.authenticated
    def get(self, notebook_path):
        """get lists checkpoints for a notebook"""
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        checkpoints = nbm.list_checkpoints(name, path)
        data = jsonapi.dumps(checkpoints, default=date_default)
        self.finish(data)
    
    @web.authenticated
    def post(self, notebook_path):
        """post creates a new checkpoint"""
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        checkpoint = nbm.create_checkpoint(name, path)
        data = jsonapi.dumps(checkpoint, default=date_default)
        if path == None:
            self.set_header('Location', '{0}notebooks/{1}/checkpoints/{2}'.format(
                self.base_project_url, name, checkpoint['checkpoint_id']
                ))
        else:
            self.set_header('Location', '{0}notebooks/{1}/{2}/checkpoints/{3}'.format(
                self.base_project_url, path, name, checkpoint['checkpoint_id']
                ))
        self.finish(data)


class ModifyNotebookCheckpointsHandler(IPythonHandler):
    
    SUPPORTED_METHODS = ('POST', 'DELETE')
    
    @web.authenticated
    def post(self, notebook_path, checkpoint_id):
        """post restores a notebook from a checkpoint"""
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        nbm.restore_checkpoint(name, checkpoint_id, path)
        self.set_status(204)
        self.finish()
    
    @web.authenticated
    def delete(self, notebook_path, checkpoint_id):
        """delete clears a checkpoint for a given notebook"""
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        nbm.delete_checkpoint(name, checkpoint_id, path)
        self.set_status(204)
        self.finish()
        
#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_path_regex = r"(?P<notebook_path>.+)"
_checkpoint_id_regex = r"(?P<checkpoint_id>[\w-]+)"

default_handlers = [
    (r"api/notebooks/%s/checkpoints" % _notebook_path_regex, NotebookCheckpointsHandler),
    (r"api/notebooks/%s/checkpoints/%s" % (_notebook_path_regex, _checkpoint_id_regex),
        ModifyNotebookCheckpointsHandler),
    (r"api/notebooks/%s" % _notebook_path_regex, NotebookHandler),
    (r"api/notebooks/", NotebookRootRedirect),
    (r"api/notebooks", NotebookRootHandler),
]




