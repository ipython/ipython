"""Tornado handlers for the notebook."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import datetime
import json
import logging
import os
import urllib

from tornado import web
from tornado import websocket

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class MainHandler(web.RequestHandler):
    def get(self):
        self.render('notebook.html')


class KernelHandler(web.RequestHandler):

    def get(self):
        self.write(json.dumps(self.application.kernel_ids))

    def post(self):
        kernel_id = self.application.start_kernel()
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
        files = os.listdir(os.getcwd())
        files = [file for file in files if file.endswith(".ipynb")]
        self.write(json.dumps(files))


class NotebookHandler(web.RequestHandler):

    SUPPORTED_METHODS = ("GET", "DELETE", "PUT")

    def find_path(self, filename):
        filename = urllib.unquote(filename)
        if not filename.endswith('.ipynb'):
            raise web.HTTPError(400)
        path = os.path.join(os.getcwd(), filename)
        return path

    def get(self, filename):
        path = self.find_path(filename)
        if not os.path.isfile(path):
            raise web.HTTPError(404)
        info = os.stat(path)
        self.set_header("Content-Type", "application/unknown")
        self.set_header("Last-Modified", datetime.datetime.utcfromtimestamp(
            info.st_mtime))
        f = open(path, "r")
        try:
            self.finish(f.read())
        finally:
            f.close()

    def put(self, filename):
        path = self.find_path(filename)
        f = open(path, "w")
        f.write(self.request.body)
        f.close()
        self.finish()

    def delete(self, filename):
        path = self.find_path(filename)
        if not os.path.isfile(path):
            raise web.HTTPError(404)
        os.unlink(path)
        self.set_status(204)
        self.finish()





