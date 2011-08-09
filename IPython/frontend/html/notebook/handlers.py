"""Tornado handlers for the notebook."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import json
import logging
import os
import urllib

from tornado import web
from tornado import websocket

try:
    from docutils.core import publish_string
except ImportError:
    publish_string = None


#-----------------------------------------------------------------------------
# Top-level handlers
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


#-----------------------------------------------------------------------------
# Kernel handlers
#-----------------------------------------------------------------------------


class MainKernelHandler(web.RequestHandler):

    def get(self):
        rkm = self.application.routing_kernel_manager
        self.finish(json.dumps(rkm.kernel_ids))

    def post(self):
        rkm = self.application.routing_kernel_manager
        notebook_id = self.get_argument('notebook', default=None)
        kernel_id = rkm.start_kernel(notebook_id)
        self.set_header('Location', '/'+kernel_id)
        self.finish(json.dumps(kernel_id))


class KernelHandler(web.RequestHandler):

    SUPPORTED_METHODS = ('DELETE')

    def delete(self, kernel_id):
        rkm = self.application.routing_kernel_manager
        rkm.kill_kernel(kernel_id)
        self.set_status(204)
        self.finish()


class KernelActionHandler(web.RequestHandler):

    def post(self, kernel_id, action):
        rkm = self.application.routing_kernel_manager
        if action == 'interrupt':
            rkm.interrupt_kernel(kernel_id)
            self.set_status(204)
        if action == 'restart':
            new_kernel_id = rkm.restart_kernel(kernel_id)
            self.write(json.dumps(new_kernel_id))
        self.finish()


class ZMQStreamHandler(websocket.WebSocketHandler):

    def initialize(self, stream_name):
        self.stream_name = stream_name

    def open(self, kernel_id):
        rkm = self.application.routing_kernel_manager
        self.router = rkm.get_router(kernel_id, self.stream_name)
        self.client_id = self.router.register_client(self)

    def on_message(self, msg):
        self.router.forward_msg(self.client_id, msg)

    def on_close(self):
        self.router.unregister_client(self.client_id)


#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------

class NotebookRootHandler(web.RequestHandler):

    def get(self):
        nbm = self.application.notebook_manager
        files = nbm.list_notebooks()
        self.finish(json.dumps(files))

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
        self.finish(json.dumps(notebook_id))


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
            self.set_header('Content-Type', 'application/xml')
            self.set_header('Content-Disposition','attachment; filename=%s.ipynb' % name)
        elif format == u'py':
            self.set_header('Content-Type', 'application/x-python')
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

#-----------------------------------------------------------------------------
# RST web service handlers
#-----------------------------------------------------------------------------

_rst_header = """========
Heading1
========

Heading2
========

Heading3
--------

Heading4
^^^^^^^^

"""

class RSTHandler(web.RequestHandler):

    def post(self):
        if publish_string is None:
            raise web.HTTPError(503)
        body = self.request.body.strip()
        source = _rst_header + body
        template_path=os.path.join(os.path.dirname(__file__), u'templates', u'rst_template.html')
        print template_path
        defaults = {'file_insertion_enabled': 0,
                    'raw_enabled': 0,
                    '_disable_config': 1,
                    'stylesheet_path': 0,
                    'initial_header_level': 3,
                    'template': template_path
        }
        try:
            html = publish_string(source, writer_name='html',
                                  settings_overrides=defaults
            )
        except:
            raise web.HTTPError(400)
        print html
#        html = '\n'.join(html.split('\n')[7:-3])
#        print html
        self.set_header('Content-Type', 'text/html')
        self.finish(html)


