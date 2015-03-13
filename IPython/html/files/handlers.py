"""Serve files directly from the ContentsManager."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import mimetypes
import json
import base64

from tornado import web

from IPython.html.base.handlers import IPythonHandler

class FilesHandler(IPythonHandler):
    """serve files via ContentsManager"""

    @web.authenticated
    def get(self, path):
        cm = self.contents_manager
        if cm.is_hidden(path):
            self.log.info("Refusing to serve hidden file, via 404 Error")
            raise web.HTTPError(404)
        
        path = path.strip('/')
        if '/' in path:
            _, name = path.rsplit('/', 1)
        else:
            name = path
        
        model = cm.get(path, type='file')
        
        if self.get_argument("download", False):
            self.set_header('Content-Disposition','attachment; filename="%s"' % name)
        
        # get mimetype from filename
        if name.endswith('.ipynb'):
            self.set_header('Content-Type', 'application/json')
        else:
            cur_mime = mimetypes.guess_type(name)[0]
            if cur_mime is not None:
                self.set_header('Content-Type', cur_mime)
        
        if model['format'] == 'base64':
            b64_bytes = model['content'].encode('ascii')
            self.write(base64.decodestring(b64_bytes))
        elif model['format'] == 'json':
            self.write(json.dumps(model['content']))
        else:
            self.write(model['content'])
        self.flush()

default_handlers = [
    (r"/files/(.*)", FilesHandler),
]