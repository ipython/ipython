# coding: utf-8
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
import random
import re
import select
import signal
import socket
import sys
import threading
import time
import uuid
import webbrowser


# Third party
# check for pyzmq 2.1.11
from IPython.utils.zmqrelated import check_for_zmq
check_for_zmq('2.1.11', 'IPython.frontend.html.notebook')

import zmq
from jinja2 import Environment, FileSystemLoader

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop import ioloop
ioloop.install()

# check for tornado 2.1.0
msg = "The IPython Notebook requires tornado >= 2.1.0"
try:
    import tornado
except ImportError:
    raise ImportError(msg)
try:
    version_info = tornado.version_info
except AttributeError:
    raise ImportError(msg + ", but you have < 1.1.0")
if version_info < (2,1,0):
    raise ImportError(msg + ", but you have %s" % tornado.version)

from tornado import httpserver
from tornado import web

# Our own libraries
from IPython.frontend.html.notebook import DEFAULT_STATIC_FILES_PATH
from .kernelmanager import MappingKernelManager
from .handlers import (LoginHandler, LogoutHandler,
    ProjectDashboardHandler, NewHandler, NamedNotebookHandler,
    MainKernelHandler, KernelHandler, KernelActionHandler, IOPubHandler, StdinHandler,
    ShellHandler, NotebookRootHandler, NotebookHandler, NotebookCopyHandler,
    AuthenticatedFileHandler, MainClusterHandler, ClusterProfileHandler, 
    ClusterActionHandler, FileFindHandler, NotebookRedirectHandler,
)
from .nbmanager import NotebookManager
from .filenbmanager import FileNotebookManager
from .clustermanager import ClusterManager

from IPython.config.application import catch_config_error, boolean_flag
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.frontend.consoleapp import IPythonConsoleApp
from IPython.kernel import swallow_argv
from IPython.kernel.zmq.session import Session, default_secure
from IPython.kernel.zmq.zmqshell import ZMQInteractiveShell
from IPython.kernel.zmq.kernelapp import (
    kernel_flags,
    kernel_aliases,
    IPKernelApp
)
from IPython.utils.importstring import import_item
from IPython.utils.localinterfaces import LOCALHOST
from IPython.utils.traitlets import (
    Dict, Unicode, Integer, List, Enum, Bool,
    DottedObjectName
)
from IPython.utils import py3compat
from IPython.utils.path import filefind

#-----------------------------------------------------------------------------
# Module globals
#-----------------------------------------------------------------------------

_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"
_kernel_action_regex = r"(?P<action>restart|interrupt)"
_notebook_id_regex = r"(?P<notebook_id>\w+-\w+-\w+-\w+-\w+)"
_notebook_name_regex = r"(?P<notebook_name>.+\.ipynb)"
_profile_regex = r"(?P<profile>[^\/]+)" # there is almost no text that is invalid
_cluster_action_regex = r"(?P<action>start|stop)"

_examples = """
ipython notebook                       # start the notebook
ipython notebook --profile=sympy       # use the sympy profile
ipython notebook --pylab=inline        # pylab in inline plotting mode
ipython notebook --certfile=mycert.pem # use SSL/TLS certificate
ipython notebook --port=5555 --ip=*    # Listen on port 5555, all interfaces
"""

#-----------------------------------------------------------------------------
# Helper functions
#-----------------------------------------------------------------------------

def url_path_join(a,b):
    if a.endswith('/') and b.startswith('/'):
        return a[:-1]+b
    else:
        return a+b

def random_ports(port, n):
    """Generate a list of n random ports near the given port.

    The first 5 ports will be sequential, and the remaining n-5 will be
    randomly selected in the range [port-2*n, port+2*n].
    """
    for i in range(min(5, n)):
        yield port + i
    for i in range(n-5):
        yield port + random.randint(-2*n, 2*n)

#-----------------------------------------------------------------------------
# The Tornado web application
#-----------------------------------------------------------------------------

class NotebookWebApplication(web.Application):

    def __init__(self, ipython_app, kernel_manager, notebook_manager,
                 cluster_manager, log,
                 base_project_url, settings_overrides):
        handlers = [
            (r"/", ProjectDashboardHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/new", NewHandler),
            (r"/%s" % _notebook_id_regex, NamedNotebookHandler),
            (r"/%s" % _notebook_name_regex, NotebookRedirectHandler),
            (r"/%s/copy" % _notebook_id_regex, NotebookCopyHandler),
            (r"/kernels", MainKernelHandler),
            (r"/kernels/%s" % _kernel_id_regex, KernelHandler),
            (r"/kernels/%s/%s" % (_kernel_id_regex, _kernel_action_regex), KernelActionHandler),
            (r"/kernels/%s/iopub" % _kernel_id_regex, IOPubHandler),
            (r"/kernels/%s/shell" % _kernel_id_regex, ShellHandler),
            (r"/kernels/%s/stdin" % _kernel_id_regex, StdinHandler),
            (r"/notebooks", NotebookRootHandler),
            (r"/notebooks/%s" % _notebook_id_regex, NotebookHandler),
            (r"/files/(.*)", AuthenticatedFileHandler, {'path' : notebook_manager.notebook_dir}),
            (r"/clusters", MainClusterHandler),
            (r"/clusters/%s/%s" % (_profile_regex, _cluster_action_regex), ClusterActionHandler),
            (r"/clusters/%s" % _profile_regex, ClusterProfileHandler),
        ]

        # Python < 2.6.5 doesn't accept unicode keys in f(**kwargs), and
        # base_project_url will always be unicode, which will in turn
        # make the patterns unicode, and ultimately result in unicode
        # keys in kwargs to handler._execute(**kwargs) in tornado.
        # This enforces that base_project_url be ascii in that situation.
        # 
        # Note that the URLs these patterns check against are escaped,
        # and thus guaranteed to be ASCII: 'héllo' is really 'h%C3%A9llo'.
        base_project_url = py3compat.unicode_to_str(base_project_url, 'ascii')
        template_path = os.path.join(os.path.dirname(__file__), "templates")
        settings = dict(
            # basics
            base_project_url=base_project_url,
            base_kernel_url=ipython_app.base_kernel_url,
            template_path=template_path,
            static_path=ipython_app.static_file_path,
            static_handler_class = FileFindHandler,
            static_url_prefix = url_path_join(base_project_url,'/static/'),
            
            # authentication
            cookie_secret=os.urandom(1024),
            login_url=url_path_join(base_project_url,'/login'),
            cookie_name='username-%s' % uuid.uuid4(),
            read_only=ipython_app.read_only,
            password=ipython_app.password,
            
            # managers
            kernel_manager=kernel_manager,
            notebook_manager=notebook_manager,
            cluster_manager=cluster_manager,
            
            # IPython stuff
            mathjax_url=ipython_app.mathjax_url,
            max_msg_size=ipython_app.max_msg_size,
            config=ipython_app.config,
            use_less=ipython_app.use_less,
            jinja2_env=Environment(loader=FileSystemLoader(template_path)),
        )

        # allow custom overrides for the tornado web app.
        settings.update(settings_overrides)

        # prepend base_project_url onto the patterns that we match
        new_handlers = []
        for handler in handlers:
            pattern = url_path_join(base_project_url, handler[0])
            new_handler = tuple([pattern] + list(handler[1:]))
            new_handlers.append(new_handler)

        super(NotebookWebApplication, self).__init__(new_handlers, **settings)



#-----------------------------------------------------------------------------
# Aliases and Flags
#-----------------------------------------------------------------------------

flags = dict(kernel_flags)
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
flags.update(boolean_flag('script', 'FileNotebookManager.save_script',
               'Auto-save a .py script everytime the .ipynb notebook is saved',
               'Do not auto-save .py scripts for every notebook'))

# the flags that are specific to the frontend
# these must be scrubbed before being passed to the kernel,
# or it will raise an error on unrecognized flags
notebook_flags = ['no-browser', 'no-mathjax', 'read-only', 'script', 'no-script']

aliases = dict(kernel_aliases)

aliases.update({
    'ip': 'NotebookApp.ip',
    'port': 'NotebookApp.port',
    'port-retries': 'NotebookApp.port_retries',
    'transport': 'KernelManager.transport',
    'keyfile': 'NotebookApp.keyfile',
    'certfile': 'NotebookApp.certfile',
    'notebook-dir': 'NotebookManager.notebook_dir',
    'browser': 'NotebookApp.browser',
})

# remove ipkernel flags that are singletons, and don't make sense in
# multi-kernel evironment:
aliases.pop('f', None)

notebook_aliases = [u'port', u'port-retries', u'ip', u'keyfile', u'certfile',
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
    
    classes = IPythonConsoleApp.classes + [MappingKernelManager, NotebookManager,
        FileNotebookManager]
    flags = Dict(flags)
    aliases = Dict(aliases)

    kernel_argv = List(Unicode)

    max_msg_size = Integer(65536, config=True, help="""
        The max raw message size accepted from the browser
        over a WebSocket connection.
    """)

    def _log_level_default(self):
        return logging.INFO

    def _log_format_default(self):
        """override default log format to include time"""
        return u"%(asctime)s.%(msecs).03d [%(name)s] %(message)s"

    # create requested profiles by default, if they don't exist:
    auto_create = Bool(True)

    # file to be opened in the notebook server
    file_to_run = Unicode('')

    # Network related information.

    ip = Unicode(LOCALHOST, config=True,
        help="The IP address the notebook server will listen on."
    )

    def _ip_changed(self, name, old, new):
        if new == u'*': self.ip = u''

    port = Integer(8888, config=True,
        help="The port the notebook server will listen on."
    )
    port_retries = Integer(50, config=True,
        help="The number of additional ports to try if the specified port is not available."
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
                        help="""Whether to open in a browser after starting.
                        The specific browser used is platform dependent and
                        determined by the python standard library `webbrowser`
                        module, unless it is overridden using the --browser
                        (NotebookApp.browser) configuration option.
                        """)

    browser = Unicode(u'', config=True,
                      help="""Specify what command to use to invoke a web
                      browser when opening the notebook. If not specified, the
                      default browser will be determined by the `webbrowser`
                      standard library module, which allows setting of the
                      BROWSER environment variable to override it.
                      """)
    
    read_only = Bool(False, config=True,
        help="Whether to prevent editing/execution of notebooks."
    )

    use_less = Bool(False, config=True,
                       help="""Wether to use Browser Side less-css parsing
                       instead of compiled css version in templates that allows
                       it. This is mainly convenient when working on the less
                       file to avoid a build step, or if user want to overwrite
                       some of the less variables without having to recompile
                       everything.
                       
                       You will need to install the less.js component in the static directory
                       either in the source tree or in your profile folder.
                       """)

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

    base_project_url = Unicode('/', config=True,
                               help='''The base URL for the notebook server.

                               Leading and trailing slashes can be omitted,
                               and will automatically be added.
                               ''')
    def _base_project_url_changed(self, name, old, new):
        if not new.startswith('/'):
            self.base_project_url = '/'+new
        elif not new.endswith('/'):
            self.base_project_url = new+'/'

    base_kernel_url = Unicode('/', config=True,
                               help='''The base URL for the kernel server

                               Leading and trailing slashes can be omitted,
                               and will automatically be added.
                               ''')
    def _base_kernel_url_changed(self, name, old, new):
        if not new.startswith('/'):
            self.base_kernel_url = '/'+new
        elif not new.endswith('/'):
            self.base_kernel_url = new+'/'

    websocket_host = Unicode("", config=True,
        help="""The hostname for the websocket server."""
    )

    extra_static_paths = List(Unicode, config=True,
        help="""Extra paths to search for serving static files.
        
        This allows adding javascript/css to be available from the notebook server machine,
        or overriding individual files in the IPython"""
    )
    def _extra_static_paths_default(self):
        return [os.path.join(self.profile_dir.location, 'static')]
    
    @property
    def static_file_path(self):
        """return extra paths + the default location"""
        return self.extra_static_paths + [DEFAULT_STATIC_FILES_PATH]

    mathjax_url = Unicode("", config=True,
        help="""The url for MathJax.js."""
    )
    def _mathjax_url_default(self):
        if not self.enable_mathjax:
            return u''
        static_url_prefix = self.webapp_settings.get("static_url_prefix",
                                                     "/static/")
        try:
            mathjax = filefind(os.path.join('mathjax', 'MathJax.js'), self.static_file_path)
        except IOError:
            if self.certfile:
                # HTTPS: load from Rackspace CDN, because SSL certificate requires it
                base = u"https://c328740.ssl.cf1.rackcdn.com"
            else:
                base = u"http://cdn.mathjax.org"
            
            url = base + u"/mathjax/latest/MathJax.js"
            self.log.info("Using MathJax from CDN: %s", url)
            return url
        else:
            self.log.info("Using local MathJax from %s" % mathjax)
            return static_url_prefix+u"mathjax/MathJax.js"
    
    def _mathjax_url_changed(self, name, old, new):
        if new and not self.enable_mathjax:
            # enable_mathjax=False overrides mathjax_url
            self.mathjax_url = u''
        else:
            self.log.info("Using MathJax: %s", new)

    notebook_manager_class = DottedObjectName('IPython.frontend.html.notebook.filenbmanager.FileNotebookManager',
        config=True,
        help='The notebook manager class to use.')

    trust_xheaders = Bool(False, config=True,
        help=("Whether to trust or not X-Scheme/X-Forwarded-Proto and X-Real-Ip/X-Forwarded-For headers"
              "sent by the upstream reverse proxy. Neccesary if the proxy handles SSL")
    )

    def parse_command_line(self, argv=None):
        super(NotebookApp, self).parse_command_line(argv)
        if argv is None:
            argv = sys.argv[1:]

        # Scrub frontend-specific flags
        self.kernel_argv = swallow_argv(argv, notebook_aliases, notebook_flags)
        # Kernel should inherit default config file from frontend
        self.kernel_argv.append("--IPKernelApp.parent_appname='%s'" % self.name)

        if self.extra_args:
            f = os.path.abspath(self.extra_args[0])
            if os.path.isdir(f):
                nbdir = f
            else:
                self.file_to_run = f
                nbdir = os.path.dirname(f)
            self.config.NotebookManager.notebook_dir = nbdir

    def init_configurables(self):
        # force Session default to be secure
        default_secure(self.config)
        self.kernel_manager = MappingKernelManager(
            config=self.config, log=self.log, kernel_argv=self.kernel_argv,
            connection_dir = self.profile_dir.security_dir,
        )
        kls = import_item(self.notebook_manager_class)
        self.notebook_manager = kls(config=self.config, log=self.log)
        self.notebook_manager.load_notebook_names()
        self.cluster_manager = ClusterManager(config=self.config, log=self.log)
        self.cluster_manager.update_profiles()

    def init_logging(self):
        # This prevents double log messages because tornado use a root logger that
        # self.log is a child of. The logging module dipatches log messages to a log
        # and all of its ancenstors until propagate is set to False.
        self.log.propagate = False
        
        # set the date format
        formatter = logging.Formatter(self.log_format, datefmt="%Y-%m-%d %H:%M:%S")
        self.log.handlers[0].setFormatter(formatter)
        
        # hook up tornado 3's loggers to our app handlers
        for name in ('access', 'application', 'general'):
            logging.getLogger('tornado.%s' % name).handlers = self.log.handlers
    
    def init_webapp(self):
        """initialize tornado webapp and httpserver"""
        self.web_app = NotebookWebApplication(
            self, self.kernel_manager, self.notebook_manager, 
            self.cluster_manager, self.log,
            self.base_project_url, self.webapp_settings
        )
        if self.certfile:
            ssl_options = dict(certfile=self.certfile)
            if self.keyfile:
                ssl_options['keyfile'] = self.keyfile
        else:
            ssl_options = None
        self.web_app.password = self.password
        self.http_server = httpserver.HTTPServer(self.web_app, ssl_options=ssl_options,
                                                 xheaders=self.trust_xheaders)
        if not self.ip:
            warning = "WARNING: The notebook server is listening on all IP addresses"
            if ssl_options is None:
                self.log.critical(warning + " and not using encryption. This"
                    "is not recommended.")
            if not self.password and not self.read_only:
                self.log.critical(warning + "and not using authentication."
                    "This is highly insecure and not recommended.")
        success = None
        for port in random_ports(self.port, self.port_retries+1):
            try:
                self.http_server.listen(port, self.ip)
            except socket.error as e:
                # XXX: remove the e.errno == -9 block when we require
                # tornado >= 3.0
                if e.errno == -9 and tornado.version_info[0] < 3:
                    # The flags passed to socket.getaddrinfo from
                    # tornado.netutils.bind_sockets can cause "gaierror:
                    # [Errno -9] Address family for hostname not supported"
                    # when the interface is not associated, for example.
                    # Changing the flags to exclude socket.AI_ADDRCONFIG does
                    # not cause this error, but the only way to do this is to
                    # monkeypatch socket to remove the AI_ADDRCONFIG attribute
                    saved_AI_ADDRCONFIG = socket.AI_ADDRCONFIG
                    self.log.warn('Monkeypatching socket to fix tornado bug')
                    del(socket.AI_ADDRCONFIG)
                    try:
                        # retry the tornado call without AI_ADDRCONFIG flags
                        self.http_server.listen(port, self.ip)
                    except socket.error as e2:
                        e = e2
                    else:
                        self.port = port
                        success = True
                        break
                    # restore the monekypatch
                    socket.AI_ADDRCONFIG = saved_AI_ADDRCONFIG
                if e.errno != errno.EADDRINUSE:
                    raise
                self.log.info('The port %i is already in use, trying another random port.' % port)
            else:
                self.port = port
                success = True
                break
        if not success:
            self.log.critical('ERROR: the notebook server could not be started because '
                              'no available port could be found.')
            self.exit(1)
    
    def init_signal(self):
        if not sys.platform.startswith('win'):
            signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGTERM, self._signal_stop)
        if hasattr(signal, 'SIGUSR1'):
            # Windows doesn't support SIGUSR1
            signal.signal(signal.SIGUSR1, self._signal_info)
        if hasattr(signal, 'SIGINFO'):
            # only on BSD-based systems
            signal.signal(signal.SIGINFO, self._signal_info)
    
    def _handle_sigint(self, sig, frame):
        """SIGINT handler spawns confirmation dialog"""
        # register more forceful signal handler for ^C^C case
        signal.signal(signal.SIGINT, self._signal_stop)
        # request confirmation dialog in bg thread, to avoid
        # blocking the App
        thread = threading.Thread(target=self._confirm_exit)
        thread.daemon = True
        thread.start()
    
    def _restore_sigint_handler(self):
        """callback for restoring original SIGINT handler"""
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    def _confirm_exit(self):
        """confirm shutdown on ^C
        
        A second ^C, or answering 'y' within 5s will cause shutdown,
        otherwise original SIGINT handler will be restored.
        
        This doesn't work on Windows.
        """
        # FIXME: remove this delay when pyzmq dependency is >= 2.1.11
        time.sleep(0.1)
        info = self.log.info
        info('interrupted')
        print self.notebook_info()
        sys.stdout.write("Shutdown this notebook server (y/[n])? ")
        sys.stdout.flush()
        r,w,x = select.select([sys.stdin], [], [], 5)
        if r:
            line = sys.stdin.readline()
            if line.lower().startswith('y'):
                self.log.critical("Shutdown confirmed")
                ioloop.IOLoop.instance().stop()
                return
        else:
            print "No answer for 5s:",
        print "resuming operation..."
        # no answer, or answer is no:
        # set it back to original SIGINT handler
        # use IOLoop.add_callback because signal.signal must be called
        # from main thread
        ioloop.IOLoop.instance().add_callback(self._restore_sigint_handler)
    
    def _signal_stop(self, sig, frame):
        self.log.critical("received signal %s, stopping", sig)
        ioloop.IOLoop.instance().stop()

    def _signal_info(self, sig, frame):
        print self.notebook_info()
    
    @catch_config_error
    def initialize(self, argv=None):
        self.init_logging()
        super(NotebookApp, self).initialize(argv)
        self.init_configurables()
        self.init_webapp()
        self.init_signal()

    def cleanup_kernels(self):
        """Shutdown all kernels.
        
        The kernels will shutdown themselves when this process no longer exists,
        but explicit shutdown allows the KernelManagers to cleanup the connection files.
        """
        self.log.info('Shutting down kernels')
        self.kernel_manager.shutdown_all()

    def notebook_info(self):
        "Return the current working directory and the server url information"
        mgr_info = self.notebook_manager.info_string() + "\n"
        return mgr_info +"The IPython Notebook is running at: %s" % self._url

    def start(self):
        """ Start the IPython Notebook server app, after initialization
        
        This method takes no arguments so all configuration and initialization
        must be done prior to calling this method."""
        ip = self.ip if self.ip else '[all ip addresses on your system]'
        proto = 'https' if self.certfile else 'http'
        info = self.log.info
        self._url = "%s://%s:%i%s" % (proto, ip, self.port,
                                      self.base_project_url)
        for line in self.notebook_info().split("\n"):
            info(line)
        info("Use Control-C to stop this server and shut down all kernels.")

        if self.open_browser or self.file_to_run:
            ip = self.ip or LOCALHOST
            try:
                browser = webbrowser.get(self.browser or None)
            except webbrowser.Error as e:
                self.log.warn('No web browser found: %s.' % e)
                browser = None

            if self.file_to_run:
                name, _ = os.path.splitext(os.path.basename(self.file_to_run))
                url = self.notebook_manager.rev_mapping.get(name, '')
            else:
                url = ''
            if browser:
                b = lambda : browser.open("%s://%s:%i%s%s" % (proto, ip,
                    self.port, self.base_project_url, url), new=2)
                threading.Thread(target=b).start()
        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            info("Interrupted...")
        finally:
            self.cleanup_kernels()
    

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def launch_new_instance():
    app = NotebookApp.instance()
    app.initialize()
    app.start()

