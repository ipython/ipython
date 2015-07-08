"""Base Tornado handlers for the notebook server."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import functools
import json
import os
import re
import sys
import traceback
try:
    # py3
    from http.client import responses
except ImportError:
    from httplib import responses
try:
    from urllib.parse import urlparse # Py 3
except ImportError:
    from urlparse import urlparse # Py 2

from jinja2 import TemplateNotFound
from tornado import web

from tornado import gen
from tornado.log import app_log


import IPython
from IPython.utils.sysinfo import get_sys_info

from IPython.config import Application
from IPython.utils.path import filefind
from IPython.utils.py3compat import string_types
from IPython.html.utils import is_hidden, url_path_join, url_escape

from IPython.html.services.security import csp_report_uri

#-----------------------------------------------------------------------------
# Top-level handlers
#-----------------------------------------------------------------------------
non_alphanum = re.compile(r'[^A-Za-z0-9]')

sys_info = json.dumps(get_sys_info())

class AuthenticatedHandler(web.RequestHandler):
    """A RequestHandler with an authenticated user."""
    
    @property
    def content_security_policy(self):
        """The default Content-Security-Policy header
        
        Can be overridden by defining Content-Security-Policy in settings['headers']
        """
        return '; '.join([
            "frame-ancestors 'self'",
            # Make sure the report-uri is relative to the base_url
            "report-uri " + url_path_join(self.base_url, csp_report_uri),
        ])

    def set_default_headers(self):
        headers = self.settings.get('headers', {})

        if "Content-Security-Policy" not in headers:
            headers["Content-Security-Policy"] = self.content_security_policy

        # Allow for overriding headers
        for header_name,value in headers.items() :
            try:
                self.set_header(header_name, value)
            except Exception as e:
                # tornado raise Exception (not a subclass)
                # if method is unsupported (websocket and Access-Control-Allow-Origin
                # for example, so just ignore)
                self.log.debug(e)
    
    def clear_login_cookie(self):
        self.clear_cookie(self.cookie_name)
    
    def get_current_user(self):
        if self.login_handler is None:
            return 'anonymous'
        return self.login_handler.get_user(self)

    @property
    def cookie_name(self):
        default_cookie_name = non_alphanum.sub('-', 'username-{}'.format(
            self.request.host
        ))
        return self.settings.get('cookie_name', default_cookie_name)
    
    @property
    def logged_in(self):
        """Is a user currently logged in?"""
        user = self.get_current_user()
        return (user and not user == 'anonymous')

    @property
    def login_handler(self):
        """Return the login handler for this application, if any."""
        return self.settings.get('login_handler_class', None)

    @property
    def login_available(self):
        """May a user proceed to log in?

        This returns True if login capability is available, irrespective of
        whether the user is already logged in or not.

        """
        if self.login_handler is None:
            return False
        return bool(self.login_handler.login_available(self.settings))


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
    def jinja_template_vars(self):
        """User-supplied values to supply to jinja templates."""
        return self.settings.get('jinja_template_vars', {})
    
    #---------------------------------------------------------------
    # URLs
    #---------------------------------------------------------------
    
    @property
    def version_hash(self):
        """The version hash to use for cache hints for static files"""
        return self.settings.get('version_hash', '')
    
    @property
    def mathjax_url(self):
        return self.settings.get('mathjax_url', '')
    
    @property
    def base_url(self):
        return self.settings.get('base_url', '/')

    @property
    def default_url(self):
        return self.settings.get('default_url', '')

    @property
    def ws_url(self):
        return self.settings.get('websocket_url', '')

    @property
    def contents_js_source(self):
        self.log.debug("Using contents: %s", self.settings.get('contents_js_source',
            'services/contents'))
        return self.settings.get('contents_js_source', 'services/contents')
    
    #---------------------------------------------------------------
    # Manager objects
    #---------------------------------------------------------------
    
    @property
    def kernel_manager(self):
        return self.settings['kernel_manager']

    @property
    def contents_manager(self):
        return self.settings['contents_manager']
    
    @property
    def cluster_manager(self):
        return self.settings['cluster_manager']
    
    @property
    def session_manager(self):
        return self.settings['session_manager']
    
    @property
    def terminal_manager(self):
        return self.settings['terminal_manager']
    
    @property
    def kernel_spec_manager(self):
        return self.settings['kernel_spec_manager']

    @property
    def config_manager(self):
        return self.settings['config_manager']

    #---------------------------------------------------------------
    # CORS
    #---------------------------------------------------------------
    
    @property
    def allow_origin(self):
        """Normal Access-Control-Allow-Origin"""
        return self.settings.get('allow_origin', '')
    
    @property
    def allow_origin_pat(self):
        """Regular expression version of allow_origin"""
        return self.settings.get('allow_origin_pat', None)
    
    @property
    def allow_credentials(self):
        """Whether to set Access-Control-Allow-Credentials"""
        return self.settings.get('allow_credentials', False)
    
    def set_default_headers(self):
        """Add CORS headers, if defined"""
        super(IPythonHandler, self).set_default_headers()
        if self.allow_origin:
            self.set_header("Access-Control-Allow-Origin", self.allow_origin)
        elif self.allow_origin_pat:
            origin = self.get_origin()
            if origin and self.allow_origin_pat.match(origin):
                self.set_header("Access-Control-Allow-Origin", origin)
        if self.allow_credentials:
            self.set_header("Access-Control-Allow-Credentials", 'true')
    
    def get_origin(self):
        # Handle WebSocket Origin naming convention differences
        # The difference between version 8 and 13 is that in 8 the
        # client sends a "Sec-Websocket-Origin" header and in 13 it's
        # simply "Origin".
        if "Origin" in self.request.headers:
            origin = self.request.headers.get("Origin")
        else:
            origin = self.request.headers.get("Sec-Websocket-Origin", None)
        return origin
    
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
            default_url=self.default_url,
            ws_url=self.ws_url,
            logged_in=self.logged_in,
            login_available=self.login_available,
            static_url=self.static_url,
            sys_info=sys_info,
            contents_js_source=self.contents_js_source,
            version_hash=self.version_hash,
            **self.jinja_template_vars
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

    def write_error(self, status_code, **kwargs):
        """render custom error pages"""
        exc_info = kwargs.get('exc_info')
        message = ''
        status_message = responses.get(status_code, 'Unknown HTTP Error')
        if exc_info:
            exception = exc_info[1]
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
        
        self.set_header('Content-Type', 'text/html')
        # render the template
        try:
            html = self.render_template('%s.html' % status_code, **ns)
        except TemplateNotFound:
            self.log.debug("No template for %d", status_code)
            html = self.render_template('error.html', **ns)
        
        self.write(html)


class APIHandler(IPythonHandler):
    """Base class for API handlers"""
    
    def check_origin(self):
        """Check Origin for cross-site API requests.
        
        Copied from WebSocket with changes:
        
        - allow unspecified host/origin (e.g. scripts)
        """
        if self.allow_origin == '*':
            return True

        host = self.request.headers.get("Host")
        origin = self.request.headers.get("Origin")

        # If no header is provided, assume it comes from a script/curl.
        # We are only concerned with cross-site browser stuff here.
        if origin is None or host is None:
            return True
        
        origin = origin.lower()
        origin_host = urlparse(origin).netloc
        
        # OK if origin matches host
        if origin_host == host:
            return True
        
        # Check CORS headers
        if self.allow_origin:
            allow = self.allow_origin == origin
        elif self.allow_origin_pat:
            allow = bool(self.allow_origin_pat.match(origin))
        else:
            # No CORS headers deny the request
            allow = False
        if not allow:
            self.log.warn("Blocking Cross Origin API request.  Origin: %s, Host: %s",
                origin, host,
            )
        return allow

    def prepare(self):
        if not self.check_origin():
            raise web.HTTPError(404)
        return super(APIHandler, self).prepare()

    @property
    def content_security_policy(self):
        csp = '; '.join([
                super(APIHandler, self).content_security_policy,
                "default-src 'none'",
            ])
        return csp
    
    def finish(self, *args, **kwargs):
        self.set_header('Content-Type', 'application/json')
        return super(APIHandler, self).finish(*args, **kwargs)


class Template404(IPythonHandler):
    """Render our 404 template"""
    def prepare(self):
        raise web.HTTPError(404)


class AuthenticatedFileHandler(IPythonHandler, web.StaticFileHandler):
    """static files should only be accessible when logged in"""

    @web.authenticated
    def get(self, path):
        if os.path.splitext(path)[1] == '.ipynb':
            name = path.rsplit('/', 1)[-1]
            self.set_header('Content-Type', 'application/json')
            self.set_header('Content-Disposition','attachment; filename="%s"' % name)
        
        return web.StaticFileHandler.get(self, path)
    
    def set_headers(self):
        super(AuthenticatedFileHandler, self).set_headers()
        # disable browser caching, rely on 304 replies for savings
        if "v" not in self.request.arguments:
            self.add_header("Cache-Control", "no-cache")
    
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
    @gen.coroutine
    def wrapper(self, *args, **kwargs):
        try:
            result = yield gen.maybe_future(method(self, *args, **kwargs))
        except web.HTTPError as e:
            self.set_header('Content-Type', 'application/json')
            status = e.status_code
            message = e.log_message
            self.log.warn(message)
            self.set_status(e.status_code)
            reply = dict(message=message, reason=e.reason)
            self.finish(json.dumps(reply))
        except Exception:
            self.set_header('Content-Type', 'application/json')
            self.log.error("Unhandled error in API request", exc_info=True)
            status = 500
            message = "Unknown server error"
            t, value, tb = sys.exc_info()
            self.set_status(status)
            tb_text = ''.join(traceback.format_exception(t, value, tb))
            reply = dict(message=message, reason=None, traceback=tb_text)
            self.finish(json.dumps(reply))
        else:
            # FIXME: can use regular return in generators in py3
            raise gen.Return(result)
    return wrapper



#-----------------------------------------------------------------------------
# File handler
#-----------------------------------------------------------------------------

# to minimize subclass changes:
HTTPError = web.HTTPError

class FileFindHandler(IPythonHandler, web.StaticFileHandler):
    """subclass of StaticFileHandler for serving files from a search path"""
    
    # cache search results, don't search for files more than once
    _static_paths = {}
    
    def set_headers(self):
        super(FileFindHandler, self).set_headers()
        # disable browser caching, rely on 304 replies for savings
        if "v" not in self.request.arguments or \
                any(self.request.path.startswith(path) for path in self.no_cache_paths):
            self.set_header("Cache-Control", "no-cache")
    
    def initialize(self, path, default_filename=None, no_cache_paths=None):
        self.no_cache_paths = no_cache_paths or []
        
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


class APIVersionHandler(APIHandler):

    @json_errors
    def get(self):
        # not authenticated, so give as few info as possible
        self.finish(json.dumps({"version":IPython.__version__}))


class TrailingSlashHandler(web.RequestHandler):
    """Simple redirect handler that strips trailing slashes
    
    This should be the first, highest priority handler.
    """
    
    def get(self):
        self.redirect(self.request.uri.rstrip('/'))
    
    post = put = get


class FilesRedirectHandler(IPythonHandler):
    """Handler for redirecting relative URLs to the /files/ handler"""
    
    @staticmethod
    def redirect_to_files(self, path):
        """make redirect logic a reusable static method
        
        so it can be called from other handlers.
        """
        cm = self.contents_manager
        if cm.dir_exists(path):
            # it's a *directory*, redirect to /tree
            url = url_path_join(self.base_url, 'tree', path)
        else:
            orig_path = path
            # otherwise, redirect to /files
            parts = path.split('/')

            if not cm.file_exists(path=path) and 'files' in parts:
                # redirect without files/ iff it would 404
                # this preserves pre-2.0-style 'files/' links
                self.log.warn("Deprecated files/ URL: %s", orig_path)
                parts.remove('files')
                path = '/'.join(parts)

            if not cm.file_exists(path=path):
                raise web.HTTPError(404)

            url = url_path_join(self.base_url, 'files', path)
        url = url_escape(url)
        self.log.debug("Redirecting %s to %s", self.request.path, url)
        self.redirect(url)
    
    def get(self, path=''):
        return self.redirect_to_files(self, path)


#-----------------------------------------------------------------------------
# URL pattern fragments for re-use
#-----------------------------------------------------------------------------

# path matches any number of `/foo[/bar...]` or just `/` or ''
path_regex = r"(?P<path>(?:(?:/[^/]+)+|/?))"

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r".*/", TrailingSlashHandler),
    (r"api", APIVersionHandler)
]
