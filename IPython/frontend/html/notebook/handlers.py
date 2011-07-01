import datetime
import json
import logging
import os
import urllib
import uuid
from Queue import Queue

from tornado import options
from tornado import web
from tornado import websocket


options.define("port", default=8888, help="run on the given port", type=int)

_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"
_kernel_action_regex = r"(?P<action>restart|interrupt)"

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


class ZMQStreamRouter(object):

    def __init__(self, zmq_stream):
        self.zmq_stream = zmq_stream
        self._clients = {}
        self.zmq_stream.on_recv(self._on_zmq_reply)

    def register_client(self, client):
        client_id = uuid.uuid4()
        self._clients[client_id] = client
        return client_id

    def unregister_client(self, client_id):
        del self._clients[client_id]

    def copy_clients(self, router):
        # Copy the clients of another router.
        for client_id, client in router._clients.items():
            client.router = self
            self._clients[client_id] = client


class IOPubStreamRouter(ZMQStreamRouter):

    def _on_zmq_reply(self, msg_list):
        for client_id, client in self._clients.items():
            for msg in msg_list:
                client.write_message(msg)

    def forward_unicode(self, client_id, msg):
        # This is a SUB stream that we should never write to.
        pass


class ShellStreamRouter(ZMQStreamRouter):

    def __init__(self, zmq_stream):
        ZMQStreamRouter.__init__(self, zmq_stream)
        self._request_queue = Queue()

    def _on_zmq_reply(self, msg_list):
        client_id = self._request_queue.get(block=False)
        client = self._clients.get(client_id)
        if client is not None:
            for msg in msg_list:
                client.write_message(msg)

    def forward_unicode(self, client_id, msg):
        self._request_queue.put(client_id)
        self.zmq_stream.send_unicode(msg)


class ZMQStreamHandler(websocket.WebSocketHandler):

    def initialize(self, stream_name):
        self.stream_name = stream_name

    def open(self, kernel_id):
        self.router = self.application.get_router(kernel_id, self.stream_name)
        self.client_id = self.router.register_client(self)
        logging.info("Connection open: %s, %s" % (kernel_id, self.client_id))

    def on_message(self, msg):
        self.router.forward_unicode(self.client_id, msg)

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





