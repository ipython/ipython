"""Tornado handlers handling general files.

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

try:
    from tornado.log import app_log
except ImportError:
    app_log = logging.getLogger()

from IPython.utils.path import filefind

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


