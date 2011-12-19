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

# stdlib
import errno
import logging
import os
import signal
import socket
import sys
import threading
import webbrowser

# Third party
import zmq

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop import ioloop
# FIXME: ioloop.install is new in pyzmq-2.1.7, so remove this conditional
# when pyzmq dependency is updated beyond that.
if hasattr(ioloop, 'install'):
    ioloop.install()
else:
    import tornado.ioloop
    tornado.ioloop.IOLoop = ioloop.IOLoop

from tornado import httpserver
from tornado import web

# Our own libraries
from .kernelmanager import MappingKernelManager
from .handlers import (LoginHandler, LogoutHandler,
    ProjectDashboardHandler, NewHandler, NamedNotebookHandler,
    MainKernelHandler, KernelHandler, KernelActionHandler, IOPubHandler,
    ShellHandler, NotebookRootHandler, NotebookHandler, RSTHandler
)
from .notebookmanager import NotebookManager

from IPython.config.application import catch_config_error, boolean_flag
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.lib.kernel import swallow_argv
from IPython.zmq.session import Session, default_secure
from IPython.zmq.zmqshell import ZMQInteractiveShell
from IPython.zmq.ipkernel import (
    flags as ipkernel_flags,
    aliases as ipkernel_aliases,
    IPKernelApp
)
from IPython.utils.traitlets import Dict, Unicode, Integer, List, Enum, Bool

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

    def __init__(self, ipython_app, kernel_manager, notebook_manager, log, settings_overrides):
        handlers = [
            (r"/", ProjectDashboardHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
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
            cookie_secret=os.urandom(1024),
            login_url="/login",
        )

        # allow custom overrides for the tornado web app.
        settings.update(settings_overrides)

        super(NotebookWebApplication, self).__init__(handlers, **settings)

        self.kernel_manager = kernel_manager
        self.log = log
        self.notebook_manager = notebook_manager
        self.ipython_app = ipython_app
        self.read_only = self.ipython_app.read_only


#-----------------------------------------------------------------------------
# Aliases and Flags
#-----------------------------------------------------------------------------

flags = dict(ipkernel_flags)
flags['no-browser']=(
    {'NotebookApp' : {'open_browser' : False}},
    "Don't open the notebook in a browser after startup."
)
flags['no-mathjax']=(
    {'NotebookApp' : {'enable_mathjax' : False}},
    """Disable MathJax
    
    MathJax is the javascript library IPython uses to render math/LaTeX. It is
    very large, so you may want to disable it if you have a slow internet
    connection, or for offline use of the notebook.
    
    When disabled, equations etc. will appear as their untransformed TeX source.
    """
)
flags['read-only'] = (
    {'NotebookApp' : {'read_only' : True}},
    """Allow read-only access to notebooks.
    
    When using a password to protect the notebook server, this flag
    allows unauthenticated clients to view the notebook list, and
    individual notebooks, but not edit them, start kernels, or run
    code.
    
    If no password is set, the server will be entirely read-only.
    """
)

# Add notebook manager flags
flags.update(boolean_flag('script', 'NotebookManager.save_script',
               'Auto-save a .py script everytime the .ipynb notebook is saved',
               'Do not auto-save .py scripts for every notebook'))

# the flags that are specific to the frontend
# these must be scrubbed before being passed to the kernel,
# or it will raise an error on unrecognized flags
notebook_flags = ['no-browser', 'no-mathjax', 'read-only', 'script', 'no-script']

aliases = dict(ipkernel_aliases)

aliases.update({
    'ip': 'NotebookApp.ip',
    'port': 'NotebookApp.port',
    'keyfile': 'NotebookApp.keyfile',
    'certfile': 'NotebookApp.certfile',
    'notebook-dir': 'NotebookManager.notebook_dir',
})

# remove ipkernel flags that are singletons, and don't make sense in
# multi-kernel evironment:
aliases.pop('f', None)

notebook_aliases = [u'port', u'ip', u'keyfile', u'certfile',
                    u'notebook-dir']

#-----------------------------------------------------------------------------
# NotebookApp
#-----------------------------------------------------------------------------

class NotebookApp(BaseIPythonApplication):

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

    port = Integer(8888, config=True,
        help="The port the notebook server will listen on."
    )

    certfile = Unicode(u'', config=True, 
        help="""The full path to an SSL/TLS certificate file."""
    )
    
    keyfile = Unicode(u'', config=True, 
        help="""The full path to a private key file for usage with SSL/TLS."""
    )

    password = Unicode(u'', config=True,
                      help="""Hashed password to use for web authentication.

                      To generate, type in a python/IPython shell:

                        from IPython.lib import passwd; passwd()

                      The string should be of the form type:salt:hashed-password.
                      """
    )
    
    open_browser = Bool(True, config=True,
                        help="Whether to open in a browser after starting.")
    
    read_only = Bool(False, config=True,
        help="Whether to prevent editing/execution of notebooks."
    )
    
    webapp_settings = Dict(config=True,
            help="Supply overrides for the tornado.web.Application that the "
                 "IPython notebook uses.")
    
    enable_mathjax = Bool(True, config=True,
        help="""Whether to enable MathJax for typesetting math/TeX

        MathJax is the javascript library IPython uses to render math/LaTeX. It is
        very large, so you may want to disable it if you have a slow internet
        connection, or for offline use of the notebook.

        When disabled, equations etc. will appear as their untransformed TeX source.
        """
    )
    def _enable_mathjax_changed(self, name, old, new):
        """set mathjax url to empty if mathjax is disabled"""
        if not new:
            self.mathjax_url = u''
    
    mathjax_url = Unicode("", config=True,
        help="""The url for MathJax.js."""
    )
    def _mathjax_url_default(self):
        if not self.enable_mathjax:
            return u''
        static_path = self.webapp_settings.get("static_path", os.path.join(os.path.dirname(__file__), "static"))
        if os.path.exists(os.path.join(static_path, 'mathjax', "MathJax.js")):
            self.log.info("Using local MathJax")
            return u"static/mathjax/MathJax.js"
        else:
            self.log.info("Using MathJax from CDN")
            return u"http://cdn.mathjax.org/mathjax/latest/MathJax.js"
    
    def _mathjax_url_changed(self, name, old, new):
        if new and not self.enable_mathjax:
            # enable_mathjax=False overrides mathjax_url
            self.mathjax_url = u''
        else:
            self.log.info("Using MathJax: %s", new)

    def parse_command_line(self, argv=None):
        super(NotebookApp, self).parse_command_line(argv)
        if argv is None:
            argv = sys.argv[1:]

        # Scrub frontend-specific flags
        self.kernel_argv = swallow_argv(argv, notebook_aliases, notebook_flags)
        # Kernel should inherit default config file from frontend
        self.kernel_argv.append("--KernelApp.parent_appname='%s'"%self.name)

    def init_configurables(self):
        # Don't let Qt or ZMQ swallow KeyboardInterupts.
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # force Session default to be secure
        default_secure(self.config)
        # Create a KernelManager and start a kernel.
        self.kernel_manager = MappingKernelManager(
            config=self.config, log=self.log, kernel_argv=self.kernel_argv,
            connection_dir = self.profile_dir.security_dir,
        )
        self.notebook_manager = NotebookManager(config=self.config, log=self.log)
        self.notebook_manager.list_notebooks()

    def init_logging(self):
        super(NotebookApp, self).init_logging()
        # This prevents double log messages because tornado use a root logger that
        # self.log is a child of. The logging module dipatches log messages to a log
        # and all of its ancenstors until propagate is set to False.
        self.log.propagate = False

    @catch_config_error
    def initialize(self, argv=None):
        super(NotebookApp, self).initialize(argv)
        self.init_configurables()
        self.web_app = NotebookWebApplication(
            self, self.kernel_manager, self.notebook_manager, self.log,
            self.webapp_settings
        )
        if self.certfile:
            ssl_options = dict(certfile=self.certfile)
            if self.keyfile:
                ssl_options['keyfile'] = self.keyfile
        else:
            ssl_options = None
        self.web_app.password = self.password
        self.http_server = httpserver.HTTPServer(self.web_app, ssl_options=ssl_options)
        if ssl_options is None and not self.ip:
            self.log.critical('WARNING: the notebook server is listening on all IP addresses '
                              'but not using any encryption or authentication. This is highly '
                              'insecure and not recommended.')

        # Try random ports centered around the default.
        from random import randint
        n = 50  # Max number of attempts, keep reasonably large.
        for port in range(self.port, self.port+5) + [self.port + randint(-2*n, 2*n) for i in range(n-5)]:
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
        info = self.log.info
        info("The IPython Notebook is running at: %s://%s:%i" % 
             (proto, ip, self.port) )
        info("Use Control-C to stop this server and shut down all kernels.")

        if self.open_browser:
            ip = self.ip or '127.0.0.1'
            b = lambda : webbrowser.open("%s://%s:%i" % (proto, ip, self.port),
                                         new=2)
            threading.Thread(target=b).start()

        ioloop.IOLoop.instance().start()

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def launch_new_instance():
    app = NotebookApp()
    app.initialize()
    app.start()

