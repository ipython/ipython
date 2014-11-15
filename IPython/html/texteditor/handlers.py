#encoding: utf-8
"""Tornado handlers for the terminal emulator."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import web
from ..base.handlers import IPythonHandler, path_regex
from ..utils import url_escape

class EditorHandler(IPythonHandler):
    """Render the text editor interface."""
    @web.authenticated
    def get(self, path):
        path = path.strip('/')
        if not self.contents_manager.file_exists(path):
            raise web.HTTPError(404, u'File does not exist: %s' % path)

        self.write(self.render_template('texteditor.html',
            file_path=url_escape(path),
            page_title=path.rsplit('/', 1)[-1] + " (editing)",
            )
        )

default_handlers = [
    (r"/texteditor%s" % path_regex, EditorHandler),
]