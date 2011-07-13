"""A tornado based IPython notebook server."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import logging
import os
import signal
import sys

import zmq

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop import ioloop
import tornado.ioloop
tornado.ioloop = ioloop

from tornado import httpserver
from tornado import web

from kernelmanager import KernelManager
from sessionmanager import SessionManager
from handlers import (
    MainHandler, KernelHandler, KernelActionHandler, ZMQStreamHandler,
    NotebookRootHandler, NotebookHandler
)
from routers import IOPubStreamRouter, ShellStreamRouter

from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.zmq.session import Session
from IPython.zmq.zmqshell import ZMQInteractiveShell
from IPython.zmq.ipkernel import (
    flags as ipkernel_flags,
    aliases as ipkernel_aliases,
    IPKernelApp
)
from IPython.utils.traitlets import Dict, Unicode, Int, Any, List, Enum

#-----------------------------------------------------------------------------
# Module globals
#-----------------------------------------------------------------------------

_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"
_kernel_action_regex = r"(?P<action>restart|interrupt)"

LOCALHOST = '127.0.0.1'

#-----------------------------------------------------------------------------
# The Tornado web application
#-----------------------------------------------------------------------------

class NotebookWebApplication(web.Application):

    def __init__(self, kernel_manager, log, kernel_argv):
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

        self.kernel_manager = kernel_manager
        self.log = log
        self.kernel_argv = kernel_argv
        self._routers = {}
        self._session_dict = {}

    #-------------------------------------------------------------------------
    # Methods for managing kernels and sessions
    #-------------------------------------------------------------------------

    @property
    def kernel_ids(self):
        return self.kernel_manager.kernel_ids

    def start_kernel(self):
        kwargs = dict()
        kwargs['extra_arguments'] = self.kernel_argv
        kernel_id = self.kernel_manager.start_kernel(**kwargs)
        self.log.info("Kernel started: %s" % kernel_id)
        self.log.debug("Kernel args: %r" % kwargs)
        self.start_session_manager(kernel_id)
        return kernel_id

    def start_session_manager(self, kernel_id):
        sm = self.kernel_manager.create_session_manager(kernel_id)
        self._session_dict[kernel_id] = sm
        iopub_stream = sm.get_iopub_stream()
        shell_stream = sm.get_shell_stream()
        iopub_router = IOPubStreamRouter(iopub_stream, sm.session)
        shell_router = ShellStreamRouter(shell_stream, sm.session)
        self._routers[(kernel_id, 'iopub')] = iopub_router
        self._routers[(kernel_id, 'shell')] = shell_router

    def kill_kernel(self, kernel_id):
        sm = self._session_dict.pop(kernel_id)
        sm.stop()
        self.kernel_manager.kill_kernel(kernel_id)
        self.log.info("Kernel killed: %s" % kernel_id)

    def interrupt_kernel(self, kernel_id):
        self.kernel_manager.interrupt_kernel(kernel_id)
        self.log.debug("Kernel interrupted: %s" % kernel_id)

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
        # self.kill_kernel(kernel_id)

        self.log.debug("Kernel restarted: %s -> %s" % (kernel_id, new_kernel_id))
        return new_kernel_id

    def get_router(self, kernel_id, stream_name):
        router = self._routers[(kernel_id, stream_name)]
        return router

    

#-----------------------------------------------------------------------------
# Aliases and Flags
#-----------------------------------------------------------------------------

flags = dict(ipkernel_flags)

# the flags that are specific to the frontend
# these must be scrubbed before being passed to the kernel,
# or it will raise an error on unrecognized flags
notebook_flags = []

aliases = dict(ipkernel_aliases)

aliases.update(dict(
    ip = 'IPythonNotebookApp.ip',
    port = 'IPythonNotebookApp.port',
    colors = 'ZMQInteractiveShell.colors',
    editor = 'RichIPythonWidget.editor',
))

#-----------------------------------------------------------------------------
# IPythonNotebookApp
#-----------------------------------------------------------------------------

class IPythonNotebookApp(BaseIPythonApplication):
    name = 'ipython-notebook'
    default_config_file_name='ipython_notebook_config.py'
    
    description = """
        The IPython HTML Notebook.
        
        This launches a Tornado based HTML Notebook Server that serves up an
        HTML5/Javascript Notebook client.
    """
    
    classes = [IPKernelApp, ZMQInteractiveShell, ProfileDir, Session,
               KernelManager, SessionManager, RichIPythonWidget]
    flags = Dict(flags)
    aliases = Dict(aliases)

    kernel_argv = List(Unicode)

    log_level = Enum((0,10,20,30,40,50,'DEBUG','INFO','WARN','ERROR','CRITICAL'),
                    default_value=logging.INFO,
                    config=True,
                    help="Set the log level by value or name.")

    # connection info:
    ip = Unicode(LOCALHOST, config=True,
        help="The IP address the notebook server will listen on."
    )

    port = Int(8888, config=True,
        help="The port the notebook server will listen on."
    )

    # the factory for creating a widget
    widget_factory = Any(RichIPythonWidget)

    def parse_command_line(self, argv=None):
        super(IPythonNotebookApp, self).parse_command_line(argv)
        if argv is None:
            argv = sys.argv[1:]

        self.kernel_argv = list(argv) # copy
        # kernel should inherit default config file from frontend
        self.kernel_argv.append("--KernelApp.parent_appname='%s'"%self.name)
        # scrub frontend-specific flags
        for a in argv:
            if a.startswith('-') and a.lstrip('-') in notebook_flags:
                self.kernel_argv.remove(a)

    def init_kernel_manager(self):
        # Don't let Qt or ZMQ swallow KeyboardInterupts.
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Create a KernelManager and start a kernel.
        self.kernel_manager = KernelManager(config=self.config, log=self.log)

    def init_logging(self):
        super(IPythonNotebookApp, self).init_logging()
        # This prevents double log messages because tornado use a root logger that
        # self.log is a child of. The logging module dipatches log messages to a log
        # and all of its ancenstors until propagate is set to False.
        self.log.propagate = False

    def initialize(self, argv=None):
        super(IPythonNotebookApp, self).initialize(argv)
        self.init_kernel_manager()
        self.web_app = NotebookWebApplication(self.kernel_manager, self.log, self.kernel_argv)
        self.http_server = httpserver.HTTPServer(self.web_app)
        self.http_server.listen(self.port)

    def start(self):
        self.log.info("The IPython Notebook is running at: http://%s:%i" % (self.ip, self.port))
        ioloop.IOLoop.instance().start()

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def launch_new_instance():
    app = IPythonNotebookApp()
    app.initialize()
    app.start()

