import json

from tornado import web

from ...base.handlers import IPythonHandler, json_errors

class NbconvertRootHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET',)

    @web.authenticated
    @json_errors
    def get(self):
        try:
            from IPython.nbconvert.exporters.export import exporter_map
        except ImportError as e:
            raise web.HTTPError(500, "Could not import nbconvert: %s" % e)
        res = {}
        for format, exporter in exporter_map.items():
            res[format] = info = {}
            info['output_mimetype'] = exporter.output_mimetype

        self.finish(json.dumps(res))

default_handlers = [
    (r"/api/nbconvert", NbconvertRootHandler),
]