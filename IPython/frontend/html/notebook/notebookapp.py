import logging
import os

import zmq

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop import ioloop
import tornado.ioloop
tornado.ioloop = ioloop

from tornado import httpserver
from tornado import options
from tornado import web

from kernelmanager import KernelManager
from handlers import (
    MainHandler, KernelHandler, KernelActionHandler, ZMQStreamHandler,
    NotebookRootHandler, NotebookHandler
)
from routers import IOPubStreamRouter, ShellStreamRouter

options.define("port", default=8888, help="run on the given port", type=int)

_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"
_kernel_action_regex = r"(?P<action>restart|interrupt)"



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
    print "The github master of tornado is required to run this server:"
    print "    https://github.com/facebook/tornado/tree/master/tornado"
    ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

