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

from zmq.eventloop import ioloop
from zmq.utils import jsonapi

from IPython.external.decorator import decorator
from IPython.zmq.session import Session
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
    if self.application.read_only:
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

    if self.application.read_only:
        return f(self, *args, **kwargs)
    else:
        return auth_f(self, *args, **kwargs)

def urljoin(*pieces):
    """Join componenet of url into a relative url

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

    def get_current_user(self):
        user_id = self.get_secure_cookie(self.settings['cookie_name'])
        # For now the user_id should not return empty, but it could eventually
        if user_id == '':
            user_id = 'anonymous'
        if user_id is None:
            # prevent extra Invalid cookie sig warnings:
            self.clear_cookie(self.settings['cookie_name'])
            if not self.application.password and not self.application.read_only:
                user_id = 'anonymous'
        return user_id

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
        return bool(self.application.password)

    @property
    def read_only(self):
        """Is the notebook read-only?

        """
        return self.application.read_only

    @property
    def ws_url(self):
        """websocket url matching the current request

        turns http[s]://host[:port] into
                ws[s]://host[:port]
        """
        proto = self.request.protocol.replace('http', 'ws')
        host = self.application.ipython_app.websocket_host # default to config value
        if host == '':
            host = self.request.host # get from request
        return "%s://%s" % (proto, host)
        

class AuthenticatedFileHandler(AuthenticatedHandler, web.StaticFileHandler):
    """static files should only be accessible when logged in"""

    @authenticate_unless_readonly
    def get(self, path):
        return web.StaticFileHandler.get(self, path)


class ProjectDashboardHandler(AuthenticatedHandler):

    @authenticate_unless_readonly
    def get(self):
        nbm = self.application.notebook_manager
        project = nbm.notebook_dir        
        template = self.application.jinja2_env.get_template('projectdashboard.html')
        self.write( template.render(project=project,
            base_project_url=self.application.ipython_app.base_project_url,
            base_kernel_url=self.application.ipython_app.base_kernel_url,
            read_only=self.read_only,
            logged_in=self.logged_in,
            login_available=self.login_available))


class LoginHandler(AuthenticatedHandler):

    def _render(self, message=None):        
        template = self.application.jinja2_env.get_template('login.html')
        self.write( template.render(
                next=url_escape(self.get_argument('next', default=self.application.ipython_app.base_project_url)),
                read_only=self.read_only,
                logged_in=self.logged_in,
                login_available=self.login_available,
                base_project_url=self.application.ipython_app.base_project_url,
                message=message
        ))

    def get(self):
        if self.current_user:
            self.redirect(self.get_argument('next', default=self.application.ipython_app.base_project_url))
        else:
            self._render()

    def post(self):
        pwd = self.get_argument('password', default=u'')
        if self.application.password:
            if passwd_check(self.application.password, pwd):
                self.set_secure_cookie(self.settings['cookie_name'], str(uuid.uuid4()))
            else:
                self._render(message={'error': 'Invalid password'})
                return

        self.redirect(self.get_argument('next', default=self.application.ipython_app.base_project_url))


class LogoutHandler(AuthenticatedHandler):

    def get(self):
        self.clear_cookie(self.settings['cookie_name'])
        if self.login_available:
            message = {'info': 'Successfully logged out.'}
        else:
            message = {'warning': 'Cannot log out.  Notebook authentication '
                       'is disabled.'}
        template = self.application.jinja2_env.get_template('logout.html')
        self.write( template.render(        
                    read_only=self.read_only,
                    logged_in=self.logged_in,
                    login_available=self.login_available,
                    base_project_url=self.application.ipython_app.base_project_url,
                    message=message))


class NewHandler(AuthenticatedHandler):

    @web.authenticated
    def get(self):
        nbm = self.application.notebook_manager
        project = nbm.notebook_dir
        notebook_id = nbm.new_notebook()
        self.redirect('/'+urljoin(self.application.ipython_app.base_project_url, notebook_id))

class NamedNotebookHandler(AuthenticatedHandler):

    @authenticate_unless_readonly
    def get(self, notebook_id):
        nbm = self.application.notebook_manager
        project = nbm.notebook_dir
        if not nbm.notebook_exists(notebook_id):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)       
        template = self.application.jinja2_env.get_template('notebook.html')
        self.write( template.render(project=project,
            notebook_id=notebook_id,
            base_project_url=self.application.ipython_app.base_project_url,
            base_kernel_url=self.application.ipython_app.base_kernel_url,
            kill_kernel=False,
            read_only=self.read_only,
            logged_in=self.logged_in,
            login_available=self.login_available,
            mathjax_url=self.application.ipython_app.mathjax_url,))


class PrintNotebookHandler(AuthenticatedHandler):

    @authenticate_unless_readonly
    def get(self, notebook_id):
        nbm = self.application.notebook_manager
        project = nbm.notebook_dir
        if not nbm.notebook_exists(notebook_id):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)        
        template = self.application.jinja2_env.get_template('printnotebook.html')
        self.write( template.render(
             project=project,
            notebook_id=notebook_id,
            base_project_url=self.application.ipython_app.base_project_url,
            base_kernel_url=self.application.ipython_app.base_kernel_url,
            kill_kernel=False,
            read_only=self.read_only,
            logged_in=self.logged_in,
            login_available=self.login_available,
            mathjax_url=self.application.ipython_app.mathjax_url,
        ))

#-----------------------------------------------------------------------------
# Kernel handlers
#-----------------------------------------------------------------------------


class MainKernelHandler(AuthenticatedHandler):

    @web.authenticated
    def get(self):
        km = self.application.kernel_manager
        self.finish(jsonapi.dumps(km.kernel_ids))

    @web.authenticated
    def post(self):
        km = self.application.kernel_manager
        nbm = self.application.notebook_manager
        notebook_id = self.get_argument('notebook', default=None)
        kernel_id = km.start_kernel(notebook_id, cwd=nbm.notebook_dir)
        data = {'ws_url':self.ws_url,'kernel_id':kernel_id}
        self.set_header('Location', '/'+kernel_id)
        self.finish(jsonapi.dumps(data))


class KernelHandler(AuthenticatedHandler):

    SUPPORTED_METHODS = ('DELETE')

    @web.authenticated
    def delete(self, kernel_id):
        km = self.application.kernel_manager
        km.shutdown_kernel(kernel_id)
        self.set_status(204)
        self.finish()


class KernelActionHandler(AuthenticatedHandler):

    @web.authenticated
    def post(self, kernel_id, action):
        km = self.application.kernel_manager
        if action == 'interrupt':
            km.interrupt_kernel(kernel_id)
            self.set_status(204)
        if action == 'restart':
            new_kernel_id = km.restart_kernel(kernel_id)
            data = {'ws_url':self.ws_url,'kernel_id':new_kernel_id}
            self.set_header('Location', '/'+new_kernel_id)
            self.write(jsonapi.dumps(data))
        self.finish()


class ZMQStreamHandler(websocket.WebSocketHandler):

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
        try:
            msg = self._reserialize_reply(msg_list)
        except Exception:
            self.application.log.critical("Malformed message: %r" % msg_list, exc_info=True)
        else:
            self.write_message(msg)

    def allow_draft76(self):
        """Allow draft 76, until browsers such as Safari update to RFC 6455.
        
        This has been disabled by default in tornado in release 2.2.0, and
        support will be removed in later versions.
        """
        return True


class AuthenticatedZMQStreamHandler(ZMQStreamHandler):

    def open(self, kernel_id):
        self.kernel_id = kernel_id.decode('ascii')
        try:
            cfg = self.application.ipython_app.config
        except AttributeError:
            # protect from the case where this is run from something other than
            # the notebook app:
            cfg = None
        self.session = Session(config=cfg)
        self.save_on_message = self.on_message
        self.on_message = self.on_first_message

    def get_current_user(self):
        user_id = self.get_secure_cookie(self.settings['cookie_name'])
        if user_id == '' or (user_id is None and not self.application.password):
            user_id = 'anonymous'
        return user_id

    def _inject_cookie_message(self, msg):
        """Inject the first message, which is the document cookie,
        for authentication."""
        if not PY3 and isinstance(msg, unicode):
            # Cookie constructor doesn't accept unicode strings
            # under Python 2.x for some reason
            msg = msg.encode('utf8', 'replace')
        try:
            self.request._cookies = Cookie.SimpleCookie(msg)
        except:
            logging.warn("couldn't parse cookie string: %s",msg, exc_info=True)

    def on_first_message(self, msg):
        self._inject_cookie_message(msg)
        if self.get_current_user() is None:
            logging.warn("Couldn't authenticate WebSocket connection")
            raise web.HTTPError(403)
        self.on_message = self.save_on_message


class IOPubHandler(AuthenticatedZMQStreamHandler):

    def initialize(self, *args, **kwargs):
        self._kernel_alive = True
        self._beating = False
        self.iopub_stream = None
        self.hb_stream = None

    def on_first_message(self, msg):
        try:
            super(IOPubHandler, self).on_first_message(msg)
        except web.HTTPError:
            self.close()
            return
        km = self.application.kernel_manager
        self.time_to_dead = km.time_to_dead
        self.first_beat = km.first_beat
        kernel_id = self.kernel_id
        try:
            self.iopub_stream = km.create_iopub_stream(kernel_id)
            self.hb_stream = km.create_hb_stream(kernel_id)
        except web.HTTPError:
            # WebSockets don't response to traditional error codes so we
            # close the connection.
            if not self.stream.closed():
                self.stream.close()
            self.close()
        else:
            self.iopub_stream.on_recv(self._on_zmq_reply)
            self.start_hb(self.kernel_died)

    def on_message(self, msg):
        pass

    def on_close(self):
        # This method can be called twice, once by self.kernel_died and once
        # from the WebSocket close event. If the WebSocket connection is
        # closed before the ZMQ streams are setup, they could be None.
        self.stop_hb()
        if self.iopub_stream is not None and not self.iopub_stream.closed():
            self.iopub_stream.on_recv(None)
            self.iopub_stream.close()
        if self.hb_stream is not None and not self.hb_stream.closed():
            self.hb_stream.close()

    def start_hb(self, callback):
        """Start the heartbeating and call the callback if the kernel dies."""
        if not self._beating:
            self._kernel_alive = True

            def ping_or_dead():
                self.hb_stream.flush()
                if self._kernel_alive:
                    self._kernel_alive = False
                    self.hb_stream.send(b'ping')
                    # flush stream to force immediate socket send
                    self.hb_stream.flush()
                else:
                    try:
                        callback()
                    except:
                        pass
                    finally:
                        self.stop_hb()

            def beat_received(msg):
                self._kernel_alive = True

            self.hb_stream.on_recv(beat_received)
            loop = ioloop.IOLoop.instance()
            self._hb_periodic_callback = ioloop.PeriodicCallback(ping_or_dead, self.time_to_dead*1000, loop)
            loop.add_timeout(time.time()+self.first_beat, self._really_start_hb)
            self._beating= True
    
    def _really_start_hb(self):
        """callback for delayed heartbeat start
        
        Only start the hb loop if we haven't been closed during the wait.
        """
        if self._beating and not self.hb_stream.closed():
            self._hb_periodic_callback.start()

    def stop_hb(self):
        """Stop the heartbeating and cancel all related callbacks."""
        if self._beating:
            self._beating = False
            self._hb_periodic_callback.stop()
            if not self.hb_stream.closed():
                self.hb_stream.on_recv(None)

    def kernel_died(self):
        self.application.kernel_manager.delete_mapping_for_kernel(self.kernel_id)
        self.application.log.error("Kernel %s failed to respond to heartbeat", self.kernel_id)
        self.write_message(
            {'header': {'msg_type': 'status'},
             'parent_header': {},
             'content': {'execution_state':'dead'}
            }
        )
        self.on_close()


class ShellHandler(AuthenticatedZMQStreamHandler):

    def initialize(self, *args, **kwargs):
        self.shell_stream = None

    def on_first_message(self, msg):
        try:
            super(ShellHandler, self).on_first_message(msg)
        except web.HTTPError:
            self.close()
            return
        km = self.application.kernel_manager
        self.max_msg_size = km.max_msg_size
        kernel_id = self.kernel_id
        try:
            self.shell_stream = km.create_shell_stream(kernel_id)
        except web.HTTPError:
            # WebSockets don't response to traditional error codes so we
            # close the connection.
            if not self.stream.closed():
                self.stream.close()
            self.close()
        else:
            self.shell_stream.on_recv(self._on_zmq_reply)

    def on_message(self, msg):
        if len(msg) < self.max_msg_size:
            msg = jsonapi.loads(msg)
            self.session.send(self.shell_stream, msg)

    def on_close(self):
        # Make sure the stream exists and is not already closed.
        if self.shell_stream is not None and not self.shell_stream.closed():
            self.shell_stream.close()


#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------

class NotebookRootHandler(AuthenticatedHandler):

    @authenticate_unless_readonly
    def get(self):
        nbm = self.application.notebook_manager
        km = self.application.kernel_manager
        files = nbm.list_notebooks()
        for f in files :
            f['kernel_id'] = km.kernel_for_notebook(f['notebook_id'])
        self.finish(jsonapi.dumps(files))

    @web.authenticated
    def post(self):
        nbm = self.application.notebook_manager
        body = self.request.body.strip()
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        if body:
            notebook_id = nbm.save_new_notebook(body, name=name, format=format)
        else:
            notebook_id = nbm.new_notebook()
        self.set_header('Location', '/'+notebook_id)
        self.finish(jsonapi.dumps(notebook_id))


class NotebookHandler(AuthenticatedHandler):

    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    @authenticate_unless_readonly
    def get(self, notebook_id):
        nbm = self.application.notebook_manager
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
        nbm = self.application.notebook_manager
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        nbm.save_notebook(notebook_id, self.request.body, name=name, format=format)
        self.set_status(204)
        self.finish()

    @web.authenticated
    def delete(self, notebook_id):
        nbm = self.application.notebook_manager
        nbm.delete_notebook(notebook_id)
        self.set_status(204)
        self.finish()


class NotebookCopyHandler(AuthenticatedHandler):

    @web.authenticated
    def get(self, notebook_id):
        nbm = self.application.notebook_manager
        project = nbm.notebook_dir
        notebook_id = nbm.copy_notebook(notebook_id)
        self.redirect('/'+urljoin(self.application.ipython_app.base_project_url, notebook_id))


#-----------------------------------------------------------------------------
# Cluster handlers
#-----------------------------------------------------------------------------


class MainClusterHandler(AuthenticatedHandler):

    @web.authenticated
    def get(self):
        cm = self.application.cluster_manager
        self.finish(jsonapi.dumps(cm.list_profiles()))


class ClusterProfileHandler(AuthenticatedHandler):

    @web.authenticated
    def get(self, profile):
        cm = self.application.cluster_manager
        self.finish(jsonapi.dumps(cm.profile_info(profile)))


class ClusterActionHandler(AuthenticatedHandler):

    @web.authenticated
    def post(self, profile, action):
        cm = self.application.cluster_manager
        if action == 'start':
            n = self.get_argument('n',default=None)
            if n is None:
                data = cm.start_cluster(profile)
            else:
                data = cm.start_cluster(profile,int(n))
        if action == 'stop':
            data = cm.stop_cluster(profile)
        self.finish(jsonapi.dumps(data))


#-----------------------------------------------------------------------------
# RST web service handlers
#-----------------------------------------------------------------------------


class RSTHandler(AuthenticatedHandler):

    @web.authenticated
    def post(self):
        if publish_string is None:
            raise web.HTTPError(503, u'docutils not available')
        body = self.request.body.strip()
        source = body
        # template_path=os.path.join(os.path.dirname(__file__), u'templates', u'rst_template.html')
        defaults = {'file_insertion_enabled': 0,
                    'raw_enabled': 0,
                    '_disable_config': 1,
                    'stylesheet_path': 0
                    # 'template': template_path
        }
        try:
            html = publish_string(source, writer_name='html',
                                  settings_overrides=defaults
            )
        except:
            raise web.HTTPError(400, u'Invalid RST')
        print html
        self.set_header('Content-Type', 'text/html')
        self.finish(html)

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
        modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])

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
            if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
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
            logging.error("Could not find static file %r", path)
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
                    logging.error("Could not open static file %r", path)
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


