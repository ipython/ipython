"""Tornado handlers for the terminal emulator."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import web
import terminado
from ..base.handlers import IPythonHandler

class TerminalHandler(IPythonHandler):
    """Render the tree view, listing notebooks, clusters, etc."""
    @web.authenticated
    def get(self, path='', name=None):
        self.write(self.render_template('terminal.html'))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/terminal", TerminalHandler),
    (r"/terminal/websocket", terminado.TermSocket,
         {'term_manager': terminado.SingleTermManager(shell_command=['bash'])}),
    ]
