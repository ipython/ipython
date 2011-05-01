import datetime
import json
import logging
import os
import urllib
import uuid
from Queue import Queue

import zmq

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop import ioloop
import tornado.ioloop
tornado.ioloop = ioloop

from tornado import httpserver
from tornado import options
from tornado import web
from tornado import websocket

from kernelmanager import KernelManager

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


class NotebookApplication(web.Application):

    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/kernels", KernelHandler),
            (r"/kernels/%s/%s" % (_kernel_id_regex, _kernel_action_regex), KernelActionHandler),
            (r"/kernels/%s/iopub" % _kernel_id_regex, ZMQStreamHandler, dict(stream_name='iopub')),
            (r"/kernels/%s/shell" % _kernel_id_regex, ZMQStreamHandler, dict(stream_name='shell')),
            (r"/notebooks", NotebookRootHandler),
            (r"/notebooks/([^/]+)", NotebookHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )
        web.Application.__init__(self, handlers, **settings)

        self.context = zmq.Context()
        self.kernel_manager = KernelManager(self.context)
        self._session_dict = {}
        self._routers = {}

    #-------------------------------------------------------------------------
    # Methods for managing kernels and sessions
    #-------------------------------------------------------------------------

    @property
    def kernel_ids(self):
        return self.kernel_manager.kernel_ids

    def start_kernel(self):
        kernel_id = self.kernel_manager.start_kernel()
        logging.info("Kernel started: %s" % kernel_id)
        self.start_session(kernel_id)
        return kernel_id

    def interrupt_kernel(self, kernel_id):
        self.kernel_manager.interrupt_kernel(kernel_id)
        logging.info("Kernel interrupted: %s" % kernel_id)

    def restart_kernel(self, kernel_id):
        # Create the new kernel first so we can move the clients over.
        new_kernel_id = self.start_kernel()

        # Copy the clients over to the new routers.
        old_iopub_router = self.get_router(kernel_id, 'iopub')
        old_shell_router = self.get_router(kernel_id, 'shell')
        new_iopub_router = self.get_router(new_kernel_id, 'iopub')
        new_shell_router = self.get_router(new_kernel_id, 'shell')
        new_iopub_router.copy_clients(old_iopub_router)
        new_shell_router.copy_clients(old_shell_router)

        # Now shutdown the old session and the kernel.
        # TODO: This causes a hard crash in ZMQStream.close, which sets
        # self.socket to None to hastily. We will need to fix this in PyZMQ
        # itself. For now, we just leave the old kernel running :(
        # sm = self.kernel_manager.get_session_manager(kernel_id)
        # session_id = self._session_dict[kernel_id]
        # sm.stop_session(session_id)
        # self.kernel_manager.kill_kernel(kernel_id)

        logging.info("Kernel restarted")
        return new_kernel_id

    def start_session(self, kernel_id):
        sm = self.kernel_manager.get_session_manager(kernel_id)
        session_id = sm.start_session()
        self._session_dict[kernel_id] = session_id
        iopub_stream = sm.get_iopub_stream(session_id)
        shell_stream = sm.get_shell_stream(session_id)
        iopub_router = IOPubStreamRouter(iopub_stream)
        shell_router = ShellStreamRouter(shell_stream)
        self._routers[(kernel_id, session_id, 'iopub')] = iopub_router
        self._routers[(kernel_id, session_id, 'shell')] = shell_router
        logging.info("Session started: %s, %s" % (kernel_id, session_id))

    def stop_session(self, kernel_id):
        # TODO: finish this!
        sm = self.kernel_manager.get_session_manager(kernel_id)
        session_id = self._session_dict[kernel_id]

    def get_router(self, kernel_id, stream_name):
        session_id = self._session_dict[kernel_id]
        router = self._routers[(kernel_id, session_id, stream_name)]
        return router


def main():
    options.parse_command_line()
    application = NotebookApplication()
    http_server = httpserver.HTTPServer(application)
    http_server.listen(options.options.port)
    print "IPython Notebook running at: http://127.0.0.1:8888"
    ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

