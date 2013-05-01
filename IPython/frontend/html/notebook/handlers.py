"""Tornado handlers for the notebook.

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

import Cookie
import datetime
import email.utils
import hashlib
import logging
import mimetypes
import os
import stat
import threading
import time
import uuid

from tornado.escape import url_escape
from tornado import web
from tornado import websocket

try:
    from tornado.log import app_log
except ImportError:
    app_log = logging.getLogger()

from zmq.eventloop import ioloop
from zmq.utils import jsonapi

from IPython.config import Application
from IPython.external.decorator import decorator
from IPython.kernel.zmq.session import Session
from IPython.lib.security import passwd_check
from IPython.utils.jsonutil import date_default
from IPython.utils.path import filefind
from IPython.utils.py3compat import PY3

try:
    from docutils.core import publish_string
except ImportError:
    publish_string = None

#-----------------------------------------------------------------------------
# Monkeypatch for Tornado <= 2.1.1 - Remove when no longer necessary!
#-----------------------------------------------------------------------------

# Google Chrome, as of release 16, changed its websocket protocol number.  The
# parts tornado cares about haven't really changed, so it's OK to continue
# accepting Chrome connections, but as of Tornado 2.1.1 (the currently released
# version as of Oct 30/2011) the version check fails, see the issue report:

# https://github.com/facebook/tornado/issues/385

# This issue has been fixed in Tornado post 2.1.1:

# https://github.com/facebook/tornado/commit/84d7b458f956727c3b0d6710

# Here we manually apply the same patch as above so that users of IPython can
# continue to work with an officially released Tornado.  We make the
# monkeypatch version check as narrow as possible to limit its effects; once
# Tornado 2.1.1 is no longer found in the wild we'll delete this code.

import tornado

if tornado.version_info <= (2,1,1):

    def _execute(self, transforms, *args, **kwargs):
        from tornado.websocket import WebSocketProtocol8, WebSocketProtocol76
        
        self.open_args = args
        self.open_kwargs = kwargs

        # The difference between version 8 and 13 is that in 8 the
        # client sends a "Sec-Websocket-Origin" header and in 13 it's
        # simply "Origin".
        if self.request.headers.get("Sec-WebSocket-Version") in ("7", "8", "13"):
            self.ws_connection = WebSocketProtocol8(self)
            self.ws_connection.accept_connection()
            
        elif self.request.headers.get("Sec-WebSocket-Version"):
            self.stream.write(tornado.escape.utf8(
                "HTTP/1.1 426 Upgrade Required\r\n"
                "Sec-WebSocket-Version: 8\r\n\r\n"))
            self.stream.close()
            
        else:
            self.ws_connection = WebSocketProtocol76(self)
            self.ws_connection.accept_connection()

    websocket.WebSocketHandler._execute = _execute
    del _execute

#-----------------------------------------------------------------------------
# Decorator for disabling read-only handlers
#-----------------------------------------------------------------------------

@decorator
def not_if_readonly(f, self, *args, **kwargs):
    if self.settings.get('read_only', False):
        raise web.HTTPError(403, "Notebook server is read-only")
    else:
        return f(self, *args, **kwargs)

@decorator
def authenticate_unless_readonly(f, self, *args, **kwargs):
    """authenticate this page *unless* readonly view is active.
    
    In read-only mode, the notebook list and print view should
    be accessible without authentication.
    """
    
    @web.authenticated
    def auth_f(self, *args, **kwargs):
        return f(self, *args, **kwargs)

    if self.settings.get('read_only', False):
        return f(self, *args, **kwargs)
    else:
        return auth_f(self, *args, **kwargs)

def urljoin(*pieces):
    """Join components of url into a relative url

    Use to prevent double slash when joining subpath
    """
    striped = [s.strip('/') for s in pieces]
    return '/'.join(s for s in striped if s)

#-----------------------------------------------------------------------------
# Top-level handlers
#-----------------------------------------------------------------------------

class RequestHandler(web.RequestHandler):
    """RequestHandler with default variable setting."""

    def render(*args, **kwargs):
        kwargs.setdefault('message', '')
        return web.RequestHandler.render(*args, **kwargs)

class AuthenticatedHandler(RequestHandler):
    """A RequestHandler with an authenticated user."""

    def clear_login_cookie(self):
        self.clear_cookie(self.cookie_name)
    
    def get_current_user(self):
        user_id = self.get_secure_cookie(self.cookie_name)
        # For now the user_id should not return empty, but it could eventually
        if user_id == '':
            user_id = 'anonymous'
        if user_id is None:
            # prevent extra Invalid cookie sig warnings:
            self.clear_login_cookie()
            if not self.read_only and not self.login_available:
                user_id = 'anonymous'
        return user_id

    @property
    def cookie_name(self):
        return self.settings.get('cookie_name', '')
    
    @property
    def password(self):
        """our password"""
        return self.settings.get('password', '')
    
    @property
    def logged_in(self):
        """Is a user currently logged in?

        """
        user = self.get_current_user()
        return (user and not user == 'anonymous')

    @property
    def login_available(self):
        """May a user proceed to log in?

        This returns True if login capability is available, irrespective of
        whether the user is already logged in or not.

        """
        return bool(self.settings.get('password', ''))

    @property
    def read_only(self):
        """Is the notebook read-only?

        """
        return self.settings.get('read_only', False)


class IPythonHandler(AuthenticatedHandler):
    """IPython-specific extensions to authenticated handling
    
    Mostly property shortcuts to IPython-specific settings.
    """
    
    @property
    def config(self):
        return self.settings.get('config', None)
    
    @property
    def log(self):
        """use the IPython log by default, falling back on tornado's logger"""
        if Application.initialized():
            return Application.instance().log
        else:
            return app_log
    
    @property
    def use_less(self):
        """Use less instead of css in templates"""
        return self.settings.get('use_less', False)
    
    #---------------------------------------------------------------
    # URLs
    #---------------------------------------------------------------
    
    @property
    def ws_url(self):
        """websocket url matching the current request

        turns http[s]://host[:port] into
                ws[s]://host[:port]
        """
        proto = self.request.protocol.replace('http', 'ws')
        host = self.settings.get('websocket_host', '')
        # default to config value
        if host == '':
            host = self.request.host # get from request
        return "%s://%s" % (proto, host)
    
    @property
    def mathjax_url(self):
        return self.settings.get('mathjax_url', '')
    
    @property
    def base_project_url(self):
        return self.settings.get('base_project_url', '/')
    
    @property
    def base_kernel_url(self):
        return self.settings.get('base_kernel_url', '/')
    
    #---------------------------------------------------------------
    # Manager objects
    #---------------------------------------------------------------
    
    @property
    def kernel_manager(self):
        return self.settings['kernel_manager']

    @property
    def notebook_manager(self):
        return self.settings['notebook_manager']
    
    @property
    def cluster_manager(self):
        return self.settings['cluster_manager']
    
    @property
    def project(self):
        return self.notebook_manager.notebook_dir
    
    #---------------------------------------------------------------
    # template rendering
    #---------------------------------------------------------------
    
    def get_template(self, name):
        """Return the jinja template object for a given name"""
        return self.settings['jinja2_env'].get_template(name)
    
    def render_template(self, name, **ns):
        ns.update(self.template_namespace)
        template = self.get_template(name)
        return template.render(**ns)
    
    @property
    def template_namespace(self):
        return dict(
            base_project_url=self.base_project_url,
            base_kernel_url=self.base_kernel_url,
            read_only=self.read_only,
            logged_in=self.logged_in,
            login_available=self.login_available,
            use_less=self.use_less,
        )

class AuthenticatedFileHandler(IPythonHandler, web.StaticFileHandler):
    """static files should only be accessible when logged in"""

    @authenticate_unless_readonly
    def get(self, path):
        return web.StaticFileHandler.get(self, path)


class ProjectDashboardHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self):
        self.write(self.render_template('projectdashboard.html',
            project=self.project,
            project_component=self.project.split('/'),
        ))


class LoginHandler(IPythonHandler):

    def _render(self, message=None):
        self.write(self.render_template('login.html',
                next=url_escape(self.get_argument('next', default=self.base_project_url)),
                message=message,
        ))

    def get(self):
        if self.current_user:
            self.redirect(self.get_argument('next', default=self.base_project_url))
        else:
            self._render()

    def post(self):
        pwd = self.get_argument('password', default=u'')
        if self.login_available:
            if passwd_check(self.password, pwd):
                self.set_secure_cookie(self.cookie_name, str(uuid.uuid4()))
            else:
                self._render(message={'error': 'Invalid password'})
                return

        self.redirect(self.get_argument('next', default=self.base_project_url))


class LogoutHandler(IPythonHandler):

    def get(self):
        self.clear_login_cookie()
        if self.login_available:
            message = {'info': 'Successfully logged out.'}
        else:
            message = {'warning': 'Cannot log out.  Notebook authentication '
                       'is disabled.'}
        self.write(self.render_template('logout.html',
                    message=message))


class NewHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        notebook_id = self.notebook_manager.new_notebook()
        self.redirect('/' + urljoin(self.base_project_url, notebook_id))

class NamedNotebookHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self, notebook_id):
        nbm = self.notebook_manager
        if not nbm.notebook_exists(notebook_id):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)       
        self.write(self.render_template('notebook.html',
            project=self.project,
            notebook_id=notebook_id,
            kill_kernel=False,
            mathjax_url=self.mathjax_url,
            )
        )


#-----------------------------------------------------------------------------
# Kernel handlers
#-----------------------------------------------------------------------------


class MainKernelHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        km = self.kernel_manager
        self.finish(jsonapi.dumps(km.list_kernel_ids()))

    @web.authenticated
    def post(self):
        km = self.kernel_manager
        nbm = self.notebook_manager
        notebook_id = self.get_argument('notebook', default=None)
        kernel_id = km.start_kernel(notebook_id, cwd=nbm.notebook_dir)
        data = {'ws_url':self.ws_url,'kernel_id':kernel_id}
        self.set_header('Location', '/'+kernel_id)
        self.finish(jsonapi.dumps(data))


class KernelHandler(IPythonHandler):

    SUPPORTED_METHODS = ('DELETE')

    @web.authenticated
    def delete(self, kernel_id):
        km = self.kernel_manager
        km.shutdown_kernel(kernel_id)
        self.set_status(204)
        self.finish()


class KernelActionHandler(IPythonHandler):

    @web.authenticated
    def post(self, kernel_id, action):
        km = self.kernel_manager
        if action == 'interrupt':
            km.interrupt_kernel(kernel_id)
            self.set_status(204)
        if action == 'restart':
            km.restart_kernel(kernel_id)
            data = {'ws_url':self.ws_url, 'kernel_id':kernel_id}
            self.set_header('Location', '/'+kernel_id)
            self.write(jsonapi.dumps(data))
        self.finish()


class ZMQStreamHandler(websocket.WebSocketHandler):
    
    def clear_cookie(self, *args, **kwargs):
        """meaningless for websockets"""
        pass

    def _reserialize_reply(self, msg_list):
        """Reserialize a reply message using JSON.

        This takes the msg list from the ZMQ socket, unserializes it using
        self.session and then serializes the result using JSON. This method
        should be used by self._on_zmq_reply to build messages that can
        be sent back to the browser.
        """
        idents, msg_list = self.session.feed_identities(msg_list)
        msg = self.session.unserialize(msg_list)
        try:
            msg['header'].pop('date')
        except KeyError:
            pass
        try:
            msg['parent_header'].pop('date')
        except KeyError:
            pass
        msg.pop('buffers')
        return jsonapi.dumps(msg, default=date_default)

    def _on_zmq_reply(self, msg_list):
        # Sometimes this gets triggered when the on_close method is scheduled in the
        # eventloop but hasn't been called.
        if self.stream.closed(): return
        try:
            msg = self._reserialize_reply(msg_list)
        except Exception:
            self.log.critical("Malformed message: %r" % msg_list, exc_info=True)
        else:
            self.write_message(msg)

    def allow_draft76(self):
        """Allow draft 76, until browsers such as Safari update to RFC 6455.
        
        This has been disabled by default in tornado in release 2.2.0, and
        support will be removed in later versions.
        """
        return True


class AuthenticatedZMQStreamHandler(ZMQStreamHandler, IPythonHandler):

    def open(self, kernel_id):
        self.kernel_id = kernel_id.decode('ascii')
        self.session = Session(config=self.config)
        self.save_on_message = self.on_message
        self.on_message = self.on_first_message

    def _inject_cookie_message(self, msg):
        """Inject the first message, which is the document cookie,
        for authentication."""
        if not PY3 and isinstance(msg, unicode):
            # Cookie constructor doesn't accept unicode strings
            # under Python 2.x for some reason
            msg = msg.encode('utf8', 'replace')
        try:
            identity, msg = msg.split(':', 1)
            self.session.session = identity.decode('ascii')
        except Exception:
            logging.error("First ws message didn't have the form 'identity:[cookie]' - %r", msg)
        
        try:
            self.request._cookies = Cookie.SimpleCookie(msg)
        except:
            self.log.warn("couldn't parse cookie string: %s",msg, exc_info=True)

    def on_first_message(self, msg):
        self._inject_cookie_message(msg)
        if self.get_current_user() is None:
            self.log.warn("Couldn't authenticate WebSocket connection")
            raise web.HTTPError(403)
        self.on_message = self.save_on_message


class ZMQChannelHandler(AuthenticatedZMQStreamHandler):
    
    @property
    def max_msg_size(self):
        return self.settings.get('max_msg_size', 65535)
    
    def create_stream(self):
        km = self.kernel_manager
        meth = getattr(km, 'connect_%s' % self.channel)
        self.zmq_stream = meth(self.kernel_id, identity=self.session.bsession)
    
    def initialize(self, *args, **kwargs):
        self.zmq_stream = None
    
    def on_first_message(self, msg):
        try:
            super(ZMQChannelHandler, self).on_first_message(msg)
        except web.HTTPError:
            self.close()
            return
        try:
            self.create_stream()
        except web.HTTPError:
            # WebSockets don't response to traditional error codes so we
            # close the connection.
            if not self.stream.closed():
                self.stream.close()
            self.close()
        else:
            self.zmq_stream.on_recv(self._on_zmq_reply)

    def on_message(self, msg):
        if len(msg) < self.max_msg_size:
            msg = jsonapi.loads(msg)
            self.session.send(self.zmq_stream, msg)

    def on_close(self):
        # This method can be called twice, once by self.kernel_died and once
        # from the WebSocket close event. If the WebSocket connection is
        # closed before the ZMQ streams are setup, they could be None.
        if self.zmq_stream is not None and not self.zmq_stream.closed():
            self.zmq_stream.on_recv(None)
            self.zmq_stream.close()


class IOPubHandler(ZMQChannelHandler):
    channel = 'iopub'
    
    def create_stream(self):
        super(IOPubHandler, self).create_stream()
        km = self.kernel_manager
        km.add_restart_callback(self.kernel_id, self.on_kernel_restarted)
        km.add_restart_callback(self.kernel_id, self.on_restart_failed, 'dead')
    
    def on_close(self):
        km = self.kernel_manager
        if self.kernel_id in km:
            km.remove_restart_callback(
                self.kernel_id, self.on_kernel_restarted,
            )
            km.remove_restart_callback(
                self.kernel_id, self.on_restart_failed, 'dead',
            )
        super(IOPubHandler, self).on_close()
    
    def _send_status_message(self, status):
        msg = self.session.msg("status",
            {'execution_state': status}
        )
        self.write_message(jsonapi.dumps(msg, default=date_default))

    def on_kernel_restarted(self):
        logging.warn("kernel %s restarted", self.kernel_id)
        self._send_status_message('restarting')

    def on_restart_failed(self):
        logging.error("kernel %s restarted failed!", self.kernel_id)
        self._send_status_message('dead')
    
    def on_message(self, msg):
        """IOPub messages make no sense"""
        pass

class ShellHandler(ZMQChannelHandler):
    channel = 'shell'

class StdinHandler(ZMQChannelHandler):
    channel = 'stdin'


#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------

class NotebookRedirectHandler(IPythonHandler):
    
    @authenticate_unless_readonly
    def get(self, notebook_name):
        # strip trailing .ipynb:
        notebook_name = os.path.splitext(notebook_name)[0]
        notebook_id = self.notebook_manager.rev_mapping.get(notebook_name, '')
        if notebook_id:
            url = self.settings.get('base_project_url', '/') + notebook_id
            return self.redirect(url)
        else:
            raise HTTPError(404)


class NotebookRootHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self):
        nbm = self.notebook_manager
        km = self.kernel_manager
        files = nbm.list_notebooks()
        for f in files :
            f['kernel_id'] = km.kernel_for_notebook(f['notebook_id'])
        self.finish(jsonapi.dumps(files))

    @web.authenticated
    def post(self):
        nbm = self.notebook_manager
        body = self.request.body.strip()
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        if body:
            notebook_id = nbm.save_new_notebook(body, name=name, format=format)
        else:
            notebook_id = nbm.new_notebook()
        self.set_header('Location', '/'+notebook_id)
        self.finish(jsonapi.dumps(notebook_id))


class NotebookHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    @authenticate_unless_readonly
    def get(self, notebook_id):
        nbm = self.notebook_manager
        format = self.get_argument('format', default='json')
        last_mod, name, data = nbm.get_notebook(notebook_id, format)
        
        if format == u'json':
            self.set_header('Content-Type', 'application/json')
            self.set_header('Content-Disposition','attachment; filename="%s.ipynb"' % name)
        elif format == u'py':
            self.set_header('Content-Type', 'application/x-python')
            self.set_header('Content-Disposition','attachment; filename="%s.py"' % name)
        self.set_header('Last-Modified', last_mod)
        self.finish(data)

    @web.authenticated
    def put(self, notebook_id):
        nbm = self.notebook_manager
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        nbm.save_notebook(notebook_id, self.request.body, name=name, format=format)
        self.set_status(204)
        self.finish()

    @web.authenticated
    def delete(self, notebook_id):
        self.notebook_manager.delete_notebook(notebook_id)
        self.set_status(204)
        self.finish()


class NotebookCopyHandler(IPythonHandler):

    @web.authenticated
    def get(self, notebook_id):
        notebook_id = self.notebook_manager.copy_notebook(notebook_id)
        self.redirect('/'+urljoin(self.base_project_url, notebook_id))


#-----------------------------------------------------------------------------
# Cluster handlers
#-----------------------------------------------------------------------------


class MainClusterHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        self.finish(jsonapi.dumps(self.cluster_manager.list_profiles()))


class ClusterProfileHandler(IPythonHandler):

    @web.authenticated
    def get(self, profile):
        self.finish(jsonapi.dumps(self.cluster_manager.profile_info(profile)))


class ClusterActionHandler(IPythonHandler):

    @web.authenticated
    def post(self, profile, action):
        cm = self.cluster_manager
        if action == 'start':
            n = self.get_argument('n',default=None)
            if n is None:
                data = cm.start_cluster(profile)
            else:
                data = cm.start_cluster(profile, int(n))
        if action == 'stop':
            data = cm.stop_cluster(profile)
        self.finish(jsonapi.dumps(data))


#-----------------------------------------------------------------------------
# File handler
#-----------------------------------------------------------------------------

# to minimize subclass changes:
HTTPError = web.HTTPError

class FileFindHandler(web.StaticFileHandler):
    """subclass of StaticFileHandler for serving files from a search path"""
    
    _static_paths = {}
    # _lock is needed for tornado < 2.2.0 compat
    _lock = threading.Lock()  # protects _static_hashes
    
    def initialize(self, path, default_filename=None):
        if isinstance(path, basestring):
            path = [path]
        self.roots = tuple(
            os.path.abspath(os.path.expanduser(p)) + os.path.sep for p in path
        )
        self.default_filename = default_filename
    
    @classmethod
    def locate_file(cls, path, roots):
        """locate a file to serve on our static file search path"""
        with cls._lock:
            if path in cls._static_paths:
                return cls._static_paths[path]
            try:
                abspath = os.path.abspath(filefind(path, roots))
            except IOError:
                # empty string should always give exists=False
                return ''
        
            # os.path.abspath strips a trailing /
            # it needs to be temporarily added back for requests to root/
            if not (abspath + os.path.sep).startswith(roots):
                raise HTTPError(403, "%s is not in root static directory", path)
        
            cls._static_paths[path] = abspath
            return abspath
    
    def get(self, path, include_body=True):
        path = self.parse_url_path(path)
        
        # begin subclass override
        abspath = self.locate_file(path, self.roots)
        # end subclass override
        
        if os.path.isdir(abspath) and self.default_filename is not None:
            # need to look at the request.path here for when path is empty
            # but there is some prefix to the path that was already
            # trimmed by the routing
            if not self.request.path.endswith("/"):
                self.redirect(self.request.path + "/")
                return
            abspath = os.path.join(abspath, self.default_filename)
        if not os.path.exists(abspath):
            raise HTTPError(404)
        if not os.path.isfile(abspath):
            raise HTTPError(403, "%s is not a file", path)

        stat_result = os.stat(abspath)
        modified = datetime.datetime.utcfromtimestamp(stat_result[stat.ST_MTIME])

        self.set_header("Last-Modified", modified)

        mime_type, encoding = mimetypes.guess_type(abspath)
        if mime_type:
            self.set_header("Content-Type", mime_type)

        cache_time = self.get_cache_time(path, modified, mime_type)

        if cache_time > 0:
            self.set_header("Expires", datetime.datetime.utcnow() + \
                                       datetime.timedelta(seconds=cache_time))
            self.set_header("Cache-Control", "max-age=" + str(cache_time))
        else:
            self.set_header("Cache-Control", "public")

        self.set_extra_headers(path)

        # Check the If-Modified-Since, and don't send the result if the
        # content has not been modified
        ims_value = self.request.headers.get("If-Modified-Since")
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.datetime(*date_tuple[:6])
            if if_since >= modified:
                self.set_status(304)
                return

        with open(abspath, "rb") as file:
            data = file.read()
            hasher = hashlib.sha1()
            hasher.update(data)
            self.set_header("Etag", '"%s"' % hasher.hexdigest())
            if include_body:
                self.write(data)
            else:
                assert self.request.method == "HEAD"
                self.set_header("Content-Length", len(data))

    @classmethod
    def get_version(cls, settings, path):
        """Generate the version string to be used in static URLs.

        This method may be overridden in subclasses (but note that it
        is a class method rather than a static method).  The default
        implementation uses a hash of the file's contents.

        ``settings`` is the `Application.settings` dictionary and ``path``
        is the relative location of the requested asset on the filesystem.
        The returned value should be a string, or ``None`` if no version
        could be determined.
        """
        # begin subclass override:
        static_paths = settings['static_path']
        if isinstance(static_paths, basestring):
            static_paths = [static_paths]
        roots = tuple(
            os.path.abspath(os.path.expanduser(p)) + os.path.sep for p in static_paths
        )

        try:
            abs_path = filefind(path, roots)
        except IOError:
            app_log.error("Could not find static file %r", path)
            return None
        
        # end subclass override
        
        with cls._lock:
            hashes = cls._static_hashes
            if abs_path not in hashes:
                try:
                    f = open(abs_path, "rb")
                    hashes[abs_path] = hashlib.md5(f.read()).hexdigest()
                    f.close()
                except Exception:
                    app_log.error("Could not open static file %r", path)
                    hashes[abs_path] = None
            hsh = hashes.get(abs_path)
            if hsh:
                return hsh[:5]
        return None


    def parse_url_path(self, url_path):
        """Converts a static URL path into a filesystem path.

        ``url_path`` is the path component of the URL with
        ``static_url_prefix`` removed.  The return value should be
        filesystem path relative to ``static_path``.
        """
        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)
        return url_path


