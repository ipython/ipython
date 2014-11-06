#encoding: utf-8
"""Tornado handlers for the terminal emulator."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import web
from ..base.handlers import IPythonHandler, file_path_regex
from ..utils import url_escape

class EditorHandler(IPythonHandler):
    """Render the terminal interface."""
    @web.authenticated
    def get(self, path, name):
        path = path.strip('/')
        if not self.contents_manager.file_exists(name, path):
            raise web.HTTPError(404, u'File does not exist: %s/%s' % (path, name))

        file_path = url_escape(path) + "/" + url_escape(name)
        self.write(self.render_template('texteditor.html',
            file_path=file_path,
            )
        )

default_handlers = [
    (r"/texteditor%s" % file_path_regex, EditorHandler),
]