#encoding: utf-8
"""Tornado handlers for the terminal emulator."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import web
from ..base.handlers import IPythonHandler, file_path_regex

class EditorHandler(IPythonHandler):
    """Render the terminal interface."""
    @web.authenticated
    def get(self, path, name):
        self.write(self.render_template('texteditor.html'))

default_handlers = [
    (r"/texteditor%s" % file_path_regex, EditorHandler),
]