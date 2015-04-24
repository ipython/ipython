#encoding: utf-8
"""Tornado handlers for the terminal emulator."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import tornado
from tornado import web
import terminado
from ..base.handlers import IPythonHandler

class TerminalHandler(IPythonHandler):
    """Render the terminal interface."""
    @web.authenticated
    def get(self, term_name):
        self.write(self.render_template('terminal.html',
                   ws_path="terminals/websocket/%s" % term_name))

class TermSocket(terminado.TermSocket, IPythonHandler):
    def set_default_headers(self):
        pass
    
    def get(self, *args, **kwargs):
        if not self.get_current_user():
            raise web.HTTPError(403)
        return super(TermSocket, self).get(*args, **kwargs)
    
    def clear_cookie(self, *args, **kwargs):
        """meaningless for websockets"""
        pass

