"""Base Tornado handlers for the notebook server."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import logging
import os
import mimetypes
import json
import base64

try:
    # py3
    from http.client import responses
except ImportError:
    from httplib import responses

from tornado import web

try:
    from tornado.log import app_log
except ImportError:
    app_log = logging.getLogger()

from IPython.html.utils import is_hidden
from IPython.html.base.handlers import IPythonHandler

class FilesHandler(IPythonHandler):
    """serve files via ContentsManager"""

    @web.authenticated
    def get(self, path):
        cm = self.settings['contents_manager']
        abs_path = os.path.join(cm.root_dir, path)
        if is_hidden(abs_path):
            self.log.info("Refusing to serve hidden file, via 404 Error")
            raise web.HTTPError(404)

        path, name = os.path.split(path)
        model = cm.get_model(name, path)

        if model['type'] == 'notebook':
            self.set_header('Content-Type', 'application/json')
        else:
            cur_mime = mimetypes.guess_type(name)[0]
            if cur_mime is not None:
                self.set_header('Content-Type', cur_mime)
        
        self.set_header('Content-Disposition','attachment; filename="%s"' % name)

        if model['format'] == 'base64':
            b64_bytes = model['content'].encode('ascii')
            self.write(base64.decodestring(b64_bytes))
        elif model['format'] == 'json':
            self.write(json.dumps(model['content']))
        else:
            self.write(model['content'])
        self.flush()

