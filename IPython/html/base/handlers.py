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


import functools
import json
import logging
import os
import stat
import sys
import traceback

from tornado import web

try:
    from tornado.log import app_log
except ImportError:
    app_log = logging.getLogger()

from IPython.config import Application
from IPython.utils.path import filefind

# UF_HIDDEN is a stat flag not defined in the stat module.
# It is used by BSD to indicate hidden files.
UF_HIDDEN = getattr(stat, 'UF_HIDDEN', 32768)

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
    def session_manager(self):
        return self.settings['session_manager']
    
    @property
    def project_dir(self):
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

    def get_json_body(self):
        """Return the body of the request as JSON data."""
        if not self.request.body:
            return None
        # Do we need to call body.decode('utf-8') here?
        body = self.request.body.strip().decode(u'utf-8')
        try:
            model = json.loads(body)
        except Exception:
            self.log.debug("Bad JSON: %r", body)
            self.log.error("Couldn't parse JSON", exc_info=True)
            raise web.HTTPError(400, u'Invalid JSON in body of request')
        return model


class AuthenticatedFileHandler(IPythonHandler, web.StaticFileHandler):
    """static files should only be accessible when logged in"""

    @web.authenticated
    def get(self, path):
        if os.path.splitext(path)[1] == '.ipynb':
            name = os.path.basename(path)
            self.set_header('Content-Type', 'application/json')
            self.set_header('Content-Disposition','attachment; filename="%s"' % name)
        
        return web.StaticFileHandler.get(self, path)
    
    def validate_absolute_path(self, root, absolute_path):
        """Validate and return the absolute path.
        
        Requires tornado 3.1
        
        Adding to tornado's own handling, forbids the serving of hidden files.
        """
        abs_path = super(AuthenticatedFileHandler, self).validate_absolute_path(root, absolute_path)
        abs_root = os.path.abspath(root)
        self.forbid_hidden(abs_root, abs_path)
        return abs_path
    
    def forbid_hidden(self, absolute_root, absolute_path):
        """Raise 403 if a file is hidden or contained in a hidden directory.
        
        Hidden is determined by either name starting with '.'
        or the UF_HIDDEN flag as reported by stat
        """
        inside_root = absolute_path[len(absolute_root):]
        if any(part.startswith('.') for part in inside_root.split(os.sep)):
            raise web.HTTPError(403)
        
        # check UF_HIDDEN on any location up to root
        path = absolute_path
        while path and path.startswith(absolute_root) and path != absolute_root:
            st = os.stat(path)
            if getattr(st, 'st_flags', 0) & UF_HIDDEN:
                raise web.HTTPError(403)
            path = os.path.dirname(path)
        
        return absolute_path


def json_errors(method):
    """Decorate methods with this to return GitHub style JSON errors.
    
    This should be used on any JSON API on any handler method that can raise HTTPErrors.
    
    This will grab the latest HTTPError exception using sys.exc_info
    and then:
    
    1. Set the HTTP status code based on the HTTPError
    2. Create and return a JSON body with a message field describing
       the error in a human readable form.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            result = method(self, *args, **kwargs)
        except web.HTTPError as e:
            status = e.status_code
            message = e.log_message
            self.set_status(e.status_code)
            self.finish(json.dumps(dict(message=message)))
        except Exception:
            self.log.error("Unhandled error in API request", exc_info=True)
            status = 500
            message = "Unknown server error"
            t, value, tb = sys.exc_info()
            self.set_status(status)
            tb_text = ''.join(traceback.format_exception(t, value, tb))
            reply = dict(message=message, traceback=tb_text)
            self.finish(json.dumps(reply))
        else:
            return result
    return wrapper



#-----------------------------------------------------------------------------
# File handler
#-----------------------------------------------------------------------------

# to minimize subclass changes:
HTTPError = web.HTTPError

class FileFindHandler(web.StaticFileHandler):
    """subclass of StaticFileHandler for serving files from a search path"""
    
    # cache search results, don't search for files more than once
    _static_paths = {}
    
    def initialize(self, path, default_filename=None):
        if isinstance(path, basestring):
            path = [path]
        
        self.root = tuple(
            os.path.abspath(os.path.expanduser(p)) + os.sep for p in path
        )
        self.default_filename = default_filename
    
    @classmethod
    def get_absolute_path(cls, roots, path):
        """locate a file to serve on our static file search path"""
        with cls._lock:
            if path in cls._static_paths:
                return cls._static_paths[path]
            try:
                abspath = os.path.abspath(filefind(path, roots))
            except IOError:
                # IOError means not found
                raise web.HTTPError(404)
            
            cls._static_paths[path] = abspath
            return abspath
    
    def validate_absolute_path(self, root, absolute_path):
        """check if the file should be served (raises 404, 403, etc.)"""
        for root in self.root:
            if (absolute_path + os.sep).startswith(root):
                break
        
        return super(FileFindHandler, self).validate_absolute_path(root, absolute_path)


class TrailingSlashHandler(web.RequestHandler):
    """Simple redirect handler that strips trailing slashes
    
    This should be the first, highest priority handler.
    """
    
    SUPPORTED_METHODS = ['GET']
    
    def get(self):
        self.redirect(self.request.uri.rstrip('/'))

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r".*/", TrailingSlashHandler)
]
