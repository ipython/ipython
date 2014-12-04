import json
from tornado import web
from ..base.handlers import IPythonHandler, json_errors
from ..utils import url_path_join

class TerminalRootHandler(IPythonHandler):
    @web.authenticated
    @json_errors
    def get(self):
        tm = self.terminal_manager
        terms = [{'name': name} for name in tm.terminals]
        self.finish(json.dumps(terms))

    @web.authenticated
    @json_errors
    def post(self):
        """POST /terminals creates a new terminal and redirects to it"""
        name, _ = self.terminal_manager.new_named_terminal()
        self.finish(json.dumps({'name': name}))


class TerminalHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET', 'DELETE')

    @web.authenticated
    @json_errors
    def get(self, name):
        tm = self.terminal_manager
        if name in tm.terminals:
            self.finish(json.dumps({'name': name}))
        else:
            raise web.HTTPError(404, "Terminal not found: %r" % name)

    @web.authenticated
    @json_errors
    def delete(self, name):
        tm = self.terminal_manager
        if name in tm.terminals:
            tm.kill(name)
            # XXX: Should this wait for terminal to finish before returning?
            self.set_status(204)
            self.finish()
        else:
            raise web.HTTPError(404, "Terminal not found: %r" % name)