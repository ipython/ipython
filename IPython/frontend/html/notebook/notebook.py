import json
import logging
import os
import uuid

import zmq

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop.zmqstream import ZMQStream
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
_session_id_regex = r"(?P<session_id>\w+)"


class MainHandler(web.RequestHandler):
    def get(self):
        self.render('notebook.html')


class KernelHandler(web.RequestHandler):

    def get(self):
        self.write(json.dumps(self.application.kernel_manager.kernel_ids))

    def post(self):
        kid = self.application.kernel_manager.start_kernel()
        logging.info("Starting kernel: %s" % kid)
        self.write(json.dumps(kid))


class SessionHandler(web.RequestHandler):

    def post(self, *args, **kwargs):
        kernel_id = kwargs['kernel_id']
        session_id = kwargs['session_id']
        logging.info("Starting session: %s, %s" % (kernel_id,session_id))
        km = self.application.kernel_manager
        sm = km.get_session_manager(kernel_id)
        sm.start_session(session_id)
        self.finish()


class ZMQStreamHandler(websocket.WebSocketHandler):

    stream_name = ''

    def open(self, *args, **kwargs):
        kernel_id = kwargs['kernel_id']
        session_id = kwargs['session_id']
        logging.info("Connection open: %s, %s" % (kernel_id,session_id))
        sm = self.application.kernel_manager.get_session_manager(kernel_id)
        method_name = "get_%s_stream" % self.stream_name
        method = getattr(sm, method_name)
        self.zmq_stream = method(session_id)
        self.zmq_stream.on_recv(self._on_zmq_reply)
        self.session_manager = sm
        self.session_id = session_id

    def on_message(self, msg):
        logging.info("Message received: %r" % msg)
        self.zmq_stream.send(msg)

    def on_close(self):
        logging.info("Connection closed: %s, %s" % (kernel_id,session_id))
        self.zmq_stream.close()

    def _on_zmq_reply(self, msg):
        logging.info("Message reply: %r" % msg)
        self.write_message(msg)


class IOPubStreamHandler(ZMQStreamHandler):

    stream_name = 'iopub'


class ShellStreamHandler(ZMQStreamHandler):

    stream_name = 'shell'


class NotebookApplication(web.Application):

    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/kernels", KernelHandler),
            (r"/kernels/%s/sessions/%s" % (_kernel_id_regex,_session_id_regex), SessionHandler),
            (r"/kernels/%s/sessions/%s/iopub" % (_kernel_id_regex,_session_id_regex), IOPubStreamHandler),
            (r"/kernels/%s/sessions/%s/shell" % (_kernel_id_regex,_session_id_regex), ShellStreamHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )
        web.Application.__init__(self, handlers, **settings)
        self.context = zmq.Context()
        self.kernel_manager = KernelManager(self.context)


def main():
    options.parse_command_line()
    application = NotebookApplication()
    http_server = httpserver.HTTPServer(application)
    http_server.listen(options.options.port)
    ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

