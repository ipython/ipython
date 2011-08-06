"""Tornado handlers for the notebook."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import json
import logging
import urllib

from tornado import web
from tornado import websocket


#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class NBBrowserHandler(web.RequestHandler):
    def get(self):
        nbm = self.application.notebook_manager
        project = nbm.notebook_dir
        self.render('nbbrowser.html', project=project)


class NewHandler(web.RequestHandler):
    def get(self):
        notebook_id = self.application.notebook_manager.new_notebook()
        self.render('notebook.html', notebook_id=notebook_id)


class NamedNotebookHandler(web.RequestHandler):
    def get(self, notebook_id):
        nbm = self.application.notebook_manager
        if not nbm.notebook_exists(notebook_id):
            raise web.HTTPError(404)
        self.render('notebook.html', notebook_id=notebook_id)


class KernelHandler(web.RequestHandler):

    def get(self):
        self.write(json.dumps(self.application.kernel_ids))

    def post(self):
        kernel_id = self.application.start_kernel()
        self.set_header('Location', '/'+kernel_id)
        self.write(json.dumps(kernel_id))


class KernelActionHandler(web.RequestHandler):

    def post(self, kernel_id, action):
        # TODO: figure out a better way of handling RPC style calls.
        if action == 'interrupt':
            self.application.interrupt_kernel(kernel_id)
        if action == 'restart':
            new_kernel_id = self.application.restart_kernel(kernel_id)
            self.write(json.dumps(new_kernel_id))


class ZMQStreamHandler(websocket.WebSocketHandler):

    def initialize(self, stream_name):
        self.stream_name = stream_name

    def open(self, kernel_id):
        self.router = self.application.get_router(kernel_id, self.stream_name)
        self.client_id = self.router.register_client(self)
        logging.info("Connection open: %s, %s" % (kernel_id, self.client_id))

    def on_message(self, msg):
        self.router.forward_msg(self.client_id, msg)

    def on_close(self):
        self.router.unregister_client(self.client_id)
        logging.info("Connection closed: %s" % self.client_id)


class NotebookRootHandler(web.RequestHandler):

    def get(self):
        nbm = self.application.notebook_manager
        files = nbm.list_notebooks()
        self.write(json.dumps(files))

    def post(self):
        nbm = self.application.notebook_manager
        body = self.request.body.strip()
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        if body:
            notebook_id = nbm.save_new_notebook(body, name=name, format=format)
        else:
            notebook_id = nbm.new_notebook()
        self.set_header('Location', '/'+notebook_id)
        self.write(json.dumps(notebook_id))


class NotebookHandler(web.RequestHandler):

    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    def get(self, notebook_id):
        nbm = self.application.notebook_manager
        format = self.get_argument('format', default='json')
        last_mod, name, data = nbm.get_notebook(notebook_id, format)
        if format == u'json':
            self.set_header('Content-Type', 'application/json')
            self.set_header('Content-Disposition','attachment; filename=%s.json' % name)
        elif format == u'xml':
            self.set_header('Content-Type', 'text/xml')
            self.set_header('Content-Disposition','attachment; filename=%s.ipynb' % name)
        elif format == u'py':
            self.set_header('Content-Type', 'text/plain')
            self.set_header('Content-Disposition','attachment; filename=%s.py' % name)
        self.set_header('Last-Modified', last_mod)
        self.finish(data)

    def put(self, notebook_id):
        nbm = self.application.notebook_manager
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        nbm.save_notebook(notebook_id, self.request.body, name=name, format=format)
        self.set_status(204)
        self.finish()

    def delete(self, notebook_id):
        nbm = self.application.notebook_manager
        nbm.delete_notebook(notebook_id)
        self.set_status(204)
        self.finish()

