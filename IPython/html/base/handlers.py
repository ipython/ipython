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
import re
import sys
import traceback
try:
    # py3
    from http.client import responses
except ImportError:
    from httplib import responses

from jinja2 import TemplateNotFound
from tornado import web

try:
    from tornado.log import app_log
except ImportError:
    app_log = logging.getLogger()

from IPython.config import Application
from IPython.utils.path import filefind
from IPython.utils.py3compat import string_types
from IPython.html.utils import is_hidden

#-----------------------------------------------------------------------------
# Top-level handlers
#-----------------------------------------------------------------------------
non_alphanum = re.compile(r'[^A-Za-z0-9]')

class AuthenticatedHandler(web.RequestHandler):
    """A RequestHandler with an authenticated user."""

    def set_default_headers(self):
        headers = self.settings.get('headers', {})
        for header_name,value in headers.items() :
            try:
                self.set_header(header_name, value)
            except Exception:
                # tornado raise Exception (not a subclass)
                # if method is unsupported (websocket and Access-Control-Allow-Origin
                # for example, so just ignore)
                pass
    
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
        default_cookie_name = non_alphanum.sub('-', 'username-{}'.format(
            self.request.host
        ))
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
    
    #---------------------------------------------------------------
    # URLs
    #---------------------------------------------------------------
    
    @property
    def mathjax_url(self):
        return self.settings.get('mathjax_url', '')
    
    @property
    def base_url(self):
        return self.settings.get('base_url', '/')
    
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
            base_url=self.base_url,
            logged_in=self.logged_in,
            login_available=self.login_available,
            static_url=self.static_url,
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

    def get_error_html(self, status_code, **kwargs):
        """render custom error pages"""
        exception = kwargs.get('exception')
        message = ''
        status_message = responses.get(status_code, 'Unknown HTTP Error')
        if exception:
            # get the custom message, if defined
            try:
                message = exception.log_message % exception.args
            except Exception:
                pass
            
            # construct the custom reason, if defined
            reason = getattr(exception, 'reason', '')
            if reason:
                status_message = reason
        
        # build template namespace
        ns = dict(
            status_code=status_code,
            status_message=status_message,
            message=message,
            exception=exception,
        )
        
        # render the template
        try:
            html = self.render_template('%s.html' % status_code, **ns)
        except TemplateNotFound:
            self.log.debug("No template for %d", status_code)
            html = self.render_template('error.html', **ns)
        return html


class Template404(IPythonHandler):
    """Render our 404 template"""
    def prepare(self):
        raise web.HTTPError(404)


class AuthenticatedFileHandler(IPythonHandler, web.StaticFileHandler):
    """static files should only be accessible when logged in"""

    @web.authenticated
    def get(self, path):
        if os.path.splitext(path)[1] == '.ipynb':
            name = os.path.basename(path)
            self.set_header('Content-Type', 'application/json')
            self.set_header('Content-Disposition','attachment; filename="%s"' % name)
        
        return web.StaticFileHandler.get(self, path)
    
    def compute_etag(self):
        return None
    
    def validate_absolute_path(self, root, absolute_path):
        """Validate and return the absolute path.
        
        Requires tornado 3.1
        
        Adding to tornado's own handling, forbids the serving of hidden files.
        """
        abs_path = super(AuthenticatedFileHandler, self).validate_absolute_path(root, absolute_path)
        abs_root = os.path.abspath(root)
        if is_hidden(abs_path, abs_root):
            self.log.info("Refusing to serve hidden file, via 404 Error")
            raise web.HTTPError(404)
        return abs_path


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
        if isinstance(path, string_types):
            path = [path]
        
        self.root = tuple(
            os.path.abspath(os.path.expanduser(p)) + os.sep for p in path
        )
        self.default_filename = default_filename
    
    def compute_etag(self):
        return None
    
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
                return ''
            
            cls._static_paths[path] = abspath
            return abspath
    
    def validate_absolute_path(self, root, absolute_path):
        """check if the file should be served (raises 404, 403, etc.)"""
        if absolute_path == '':
            raise web.HTTPError(404)
        
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
# URL pattern fragments for re-use
#-----------------------------------------------------------------------------

path_regex = r"(?P<path>(?:/.*)*)"
notebook_name_regex = r"(?P<name>[^/]+\.ipynb)"
notebook_path_regex = "%s/%s" % (path_regex, notebook_name_regex)

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r".*/", TrailingSlashHandler)
]
