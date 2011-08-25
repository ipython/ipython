"""A tornado based IPython notebook server.

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

import errno
import logging
import os
import signal
import socket
import sys

import zmq

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop import ioloop
import tornado.ioloop
tornado.ioloop = ioloop

from tornado import httpserver
from tornado import web

from .kernelmanager import MappingKernelManager
from .handlers import (
    NBBrowserHandler, NewHandler, NamedNotebookHandler,
    MainKernelHandler, KernelHandler, KernelActionHandler, IOPubHandler,
    ShellHandler, NotebookRootHandler, NotebookHandler, RSTHandler
)
from .notebookmanager import NotebookManager

from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.zmq.session import Session
from IPython.zmq.zmqshell import ZMQInteractiveShell
from IPython.zmq.ipkernel import (
    flags as ipkernel_flags,
    aliases as ipkernel_aliases,
    IPKernelApp
)
from IPython.utils.traitlets import Dict, Unicode, Int, List, Enum

#-----------------------------------------------------------------------------
# Module globals
#-----------------------------------------------------------------------------

_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"
_kernel_action_regex = r"(?P<action>restart|interrupt)"
_notebook_id_regex = r"(?P<notebook_id>\w+-\w+-\w+-\w+-\w+)"

LOCALHOST = '127.0.0.1'

_examples = """
ipython notebook                       # start the notebook
ipython notebook --profile=sympy       # use the sympy profile
ipython notebook --pylab=inline        # pylab in inline plotting mode
ipython notebook --certfile=mycert.pem # use SSL/TLS certificate
ipython notebook --port=5555 --ip=*    # Listen on port 5555, all interfaces
"""

#-----------------------------------------------------------------------------
# The Tornado web application
#-----------------------------------------------------------------------------

class NotebookWebApplication(web.Application):

    def __init__(self, ipython_app, kernel_manager, notebook_manager, log):
        handlers = [
            (r"/", NBBrowserHandler),
            (r"/new", NewHandler),
            (r"/%s" % _notebook_id_regex, NamedNotebookHandler),
            (r"/kernels", MainKernelHandler),
            (r"/kernels/%s" % _kernel_id_regex, KernelHandler),
            (r"/kernels/%s/%s" % (_kernel_id_regex, _kernel_action_regex), KernelActionHandler),
            (r"/kernels/%s/iopub" % _kernel_id_regex, IOPubHandler),
            (r"/kernels/%s/shell" % _kernel_id_regex, ShellHandler),
            (r"/notebooks", NotebookRootHandler),
            (r"/notebooks/%s" % _notebook_id_regex, NotebookHandler),
            (r"/rstservice/render", RSTHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )
        web.Application.__init__(self, handlers, **settings)

        self.kernel_manager = kernel_manager
        self.log = log
        self.notebook_manager = notebook_manager
        self.ipython_app = ipython_app


#-----------------------------------------------------------------------------
# Aliases and Flags
#-----------------------------------------------------------------------------

flags = dict(ipkernel_flags)

# the flags that are specific to the frontend
# these must be scrubbed before being passed to the kernel,
# or it will raise an error on unrecognized flags
notebook_flags = []

aliases = dict(ipkernel_aliases)

aliases.update({
    'ip': 'IPythonNotebookApp.ip',
    'port': 'IPythonNotebookApp.port',
    'keyfile': 'IPythonNotebookApp.keyfile',
    'certfile': 'IPythonNotebookApp.certfile',
    'ws-hostname': 'IPythonNotebookApp.ws_hostname',
    'notebook-dir': 'NotebookManager.notebook_dir'
})

notebook_aliases = [u'port', u'ip', u'keyfile', u'certfile', u'ws-hostname',
                    u'notebook-dir']

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
    examples = _examples
    
    classes = [IPKernelApp, ZMQInteractiveShell, ProfileDir, Session,
               MappingKernelManager, NotebookManager]
    flags = Dict(flags)
    aliases = Dict(aliases)

    kernel_argv = List(Unicode)

    log_level = Enum((0,10,20,30,40,50,'DEBUG','INFO','WARN','ERROR','CRITICAL'),
                    default_value=logging.INFO,
                    config=True,
                    help="Set the log level by value or name.")

    # Network related information.

    ip = Unicode(LOCALHOST, config=True,
        help="The IP address the notebook server will listen on."
    )

    def _ip_changed(self, name, old, new):
        if new == u'*': self.ip = u''

    port = Int(8888, config=True,
        help="The port the notebook server will listen on."
    )

    ws_hostname = Unicode(LOCALHOST, config=True,
        help="""The FQDN or IP for WebSocket connections. The default will work
                fine when the server is listening on localhost, but this needs to
                be set if the ip option is used. It will be used as the hostname part
                of the WebSocket url: ws://hostname/path."""
    )

    certfile = Unicode(u'', config=True, 
        help="""The full path to an SSL/TLS certificate file."""
    )
    
    keyfile = Unicode(u'', config=True, 
        help="""The full path to a private key file for usage with SSL/TLS."""
    )

    def get_ws_url(self):
        """Return the WebSocket URL for this server."""
        if self.certfile:
            prefix = u'wss://'
        else:
            prefix = u'ws://'
        return prefix + self.ws_hostname + u':' + unicode(self.port)

    def parse_command_line(self, argv=None):
        super(IPythonNotebookApp, self).parse_command_line(argv)
        if argv is None:
            argv = sys.argv[1:]

        self.kernel_argv = list(argv) # copy
        # Kernel should inherit default config file from frontend
        self.kernel_argv.append("--KernelApp.parent_appname='%s'"%self.name)
        # Scrub frontend-specific flags
        for a in argv:
            if a.startswith('-') and a.lstrip('-') in notebook_flags:
                self.kernel_argv.remove(a)
        for a in argv:
            if a.startswith('-'):
                alias = a.lstrip('-').split('=')[0]
                if alias in notebook_aliases:
                    self.kernel_argv.remove(a)

    def init_configurables(self):
        # Don't let Qt or ZMQ swallow KeyboardInterupts.
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Create a KernelManager and start a kernel.
        self.kernel_manager = MappingKernelManager(
            config=self.config, log=self.log, kernel_argv=self.kernel_argv
        )
        self.notebook_manager = NotebookManager(config=self.config, log=self.log)
        self.notebook_manager.list_notebooks()

    def init_logging(self):
        super(IPythonNotebookApp, self).init_logging()
        # This prevents double log messages because tornado use a root logger that
        # self.log is a child of. The logging module dipatches log messages to a log
        # and all of its ancenstors until propagate is set to False.
        self.log.propagate = False

    def initialize(self, argv=None):
        super(IPythonNotebookApp, self).initialize(argv)
        self.init_configurables()
        self.web_app = NotebookWebApplication(
            self, self.kernel_manager, self.notebook_manager, self.log
        )
        if self.certfile:
            ssl_options = dict(certfile=self.certfile)
            if self.keyfile:
                ssl_options['keyfile'] = self.keyfile
        else:
            ssl_options = None
        self.http_server = httpserver.HTTPServer(self.web_app, ssl_options=ssl_options)
        if ssl_options is None and not self.ip:
            self.log.critical('WARNING: the notebook server is listening on all IP addresses '
                              'but not using any encryption or authentication. This is highly '
                              'insecure and not recommended.')

        # Try random ports centered around the default.
        from random import randint
        n = 50  # Max number of attempts, keep reasonably large.
        for port in [self.port] + [self.port + randint(-2*n, 2*n) for i in range(n)]:
            try:
                self.http_server.listen(port, self.ip)
            except socket.error, e:
                if e.errno != errno.EADDRINUSE:
                    raise
                self.log.info('The port %i is already in use, trying another random port.' % port)
            else:
                self.port = port
                break

    def start(self):
        ip = self.ip if self.ip else '[all ip addresses on your system]'
        proto = 'https' if self.certfile else 'http'
        self.log.info("The IPython Notebook is running at: %s://%s:%i" % (proto,
                                                                          ip,
                                                                          self.port))
        ioloop.IOLoop.instance().start()

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def launch_new_instance():
    app = IPythonNotebookApp()
    app.initialize()
    app.start()

