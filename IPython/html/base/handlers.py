"""Base Tornado handlers for the notebook.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


import datetime
import email.utils
import hashlib
import logging
import mimetypes
import os
import stat
import threading

from tornado import web
from tornado import websocket

try:
    from tornado.log import app_log
except ImportError:
    app_log = logging.getLogger()

from IPython.config import Application
from IPython.external.decorator import decorator
from IPython.utils.path import filefind

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
            if not self.login_available:
                user_id = 'anonymous'
        return user_id

    @property
    def cookie_name(self):
        default_cookie_name = 'username-{host}'.format(
            host=self.request.host,
        ).replace(':', '-')
        return self.settings.get('cookie_name', default_cookie_name)
    
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

        By default, this is just `''`, indicating that it should match
        the same host, protocol, port, etc.
        """
        return self.settings.get('websocket_url', '')
    
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
            logged_in=self.logged_in,
            login_available=self.login_available,
            use_less=self.use_less,
        )

class AuthenticatedFileHandler(IPythonHandler, web.StaticFileHandler):
    """static files should only be accessible when logged in"""

    @web.authenticated
    def get(self, path):
        return web.StaticFileHandler.get(self, path)


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

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = []
