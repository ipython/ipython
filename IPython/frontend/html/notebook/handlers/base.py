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

import logging

from tornado import web
from tornado import websocket

try:
    from tornado.log import app_log
except ImportError:
    app_log = logging.getLogger()

from IPython.config import Application
from IPython.external.decorator import decorator

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
