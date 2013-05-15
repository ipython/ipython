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

from .base import IPythonHandler, authenticate_unless_readonly

#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------

class NotebookRootHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self):
        nbm = self.notebook_manager
        km = self.kernel_manager
        files = nbm.list_notebooks()
        for f in files :
            f['kernel_id'] = km.kernel_for_notebook(f['notebook_id'])
        self.finish(jsonapi.dumps(files))

    @web.authenticated
    def post(self):
        nbm = self.notebook_manager
        body = self.request.body.strip()
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        if body:
            notebook_id = nbm.save_new_notebook(body, name=name, format=format)
        else:
            notebook_id = nbm.new_notebook()
        self.set_header('Location', '{0}notebooks/{1}'.format(self.base_project_url, notebook_id))
        self.finish(jsonapi.dumps(notebook_id))


class NotebookHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    @authenticate_unless_readonly
    def get(self, notebook_id):
        nbm = self.notebook_manager
        format = self.get_argument('format', default='json')
        last_mod, name, data = nbm.get_notebook(notebook_id, format)
        
        if format == u'json':
            self.set_header('Content-Type', 'application/json')
            self.set_header('Content-Disposition','attachment; filename="%s.ipynb"' % name)
        elif format == u'py':
            self.set_header('Content-Type', 'application/x-python')
            self.set_header('Content-Disposition','attachment; filename="%s.py"' % name)
        self.set_header('Last-Modified', last_mod)
        self.finish(data)

    @web.authenticated
    def put(self, notebook_id):
        nbm = self.notebook_manager
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        nbm.save_notebook(notebook_id, self.request.body, name=name, format=format)
        self.set_status(204)
        self.finish()

    @web.authenticated
    def delete(self, notebook_id):
        self.notebook_manager.delete_notebook(notebook_id)
        self.set_status(204)
        self.finish()


class NotebookCheckpointsHandler(IPythonHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST')
    
    @web.authenticated
    def get(self, notebook_id):
        """get lists checkpoints for a notebook"""
        nbm = self.notebook_manager
        checkpoints = nbm.list_checkpoints(notebook_id)
        data = jsonapi.dumps(checkpoints, default=date_default)
        self.finish(data)
    
    @web.authenticated
    def post(self, notebook_id):
        """post creates a new checkpoint"""
        nbm = self.notebook_manager
        checkpoint = nbm.create_checkpoint(notebook_id)
        data = jsonapi.dumps(checkpoint, default=date_default)
        self.set_header('Location', '{0}notebooks/{1}/checkpoints/{2}'.format(
            self.base_project_url, notebook_id, checkpoint['checkpoint_id']
        ))
        
        self.finish(data)


class ModifyNotebookCheckpointsHandler(IPythonHandler):
    
    SUPPORTED_METHODS = ('POST', 'DELETE')
    
    @web.authenticated
    def post(self, notebook_id, checkpoint_id):
        """post restores a notebook from a checkpoint"""
        nbm = self.notebook_manager
        nbm.restore_checkpoint(notebook_id, checkpoint_id)
        self.set_status(204)
        self.finish()
    
    @web.authenticated
    def delete(self, notebook_id, checkpoint_id):
        """delete clears a checkpoint for a given notebook"""
        nbm = self.notebook_manager
        nbm.delte_checkpoint(notebook_id, checkpoint_id)
        self.set_status(204)
        self.finish()


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_id_regex = r"(?P<notebook_id>\w+-\w+-\w+-\w+-\w+)"
_checkpoint_id_regex = r"(?P<checkpoint_id>[\w-]+)"

default_handlers = [
    (r"/notebooks", NotebookRootHandler),
    (r"/notebooks/%s" % _notebook_id_regex, NotebookHandler),
    (r"/notebooks/%s/checkpoints" % _notebook_id_regex, NotebookCheckpointsHandler),
    (r"/notebooks/%s/checkpoints/%s" % (_notebook_id_regex, _checkpoint_id_regex),
        ModifyNotebookCheckpointsHandler
    ),
]




