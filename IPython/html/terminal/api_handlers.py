import json
from tornado import web
from ..base.handlers import IPythonHandler, json_errors

class TerminalRootHandler(IPythonHandler):
    @web.authenticated
    @json_errors
    def get(self):
        tm = self.application.terminal_manager
        terms = [{'name': name} for name in tm.terminals]
        self.finish(json.dumps(terms))

class TerminalHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET', 'DELETE')

    @web.authenticated
    @json_errors
    def get(self, name):
        tm = self.application.terminal_manager
        if name in tm.terminals:
            self.finish(json.dumps({'name': name}))
        else:
            raise web.HTTPError(404, "Terminal not found: %r" % name)

    @web.authenticated
    @json_errors
    def delete(self, name):
        tm = self.application.terminal_manager
        if name in tm.terminals:
            tm.kill(name)
            # XXX: Should this wait for terminal to finish before returning?
            self.set_status(204)
            self.finish()
        else:
            raise web.HTTPError(404, "Terminal not found: %r" % name)