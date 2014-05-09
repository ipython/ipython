"""Tornado handlers for kernel specifications."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import web

from zmq.utils import jsonapi

from ...base.handlers import IPythonHandler, json_errors


class MainKernelSpecHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET',)

    @web.authenticated
    @json_errors
    def get(self):
        ksm = self.kernel_spec_manager
        results = []
        for kernel_name in ksm.find_kernel_specs():
            results.append(dict(name=kernel_name,
                display_name=ksm.get_kernel_spec(kernel_name).display_name))

        self.set_header("Content-Type", 'application/json')
        self.finish(jsonapi.dumps(results))


class KernelSpecHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET',)

    @web.authenticated
    @json_errors
    def get(self, kernel_name):
        ksm = self.kernel_spec_manager
        try:
            kernelspec = ksm.get_kernel_spec(kernel_name)
        except KeyError:
            raise web.HTTPError(404, u'Kernel spec %s not found' % kernel_name)
        self.set_header("Content-Type", 'application/json')
        self.finish(kernelspec.to_json())


class KernelSpecResourceHandler(web.StaticFileHandler, IPythonHandler):
    SUPPORTED_METHODS = ('GET', 'HEAD')

    def initialize(self):
        web.StaticFileHandler.initialize(self, path='')

    def get(self, kernel_name, path, include_body=True):
        ksm = self.kernel_spec_manager
        try:
            self.root = ksm.get_kernel_spec(kernel_name).resource_dir
        except KeyError:
            raise web.HTTPError(404, u'Kernel spec %s not found' % kernel_name)
        self.log.debug("Serving kernel resource from: %s", self.root)
        return web.StaticFileHandler.get(self, path, include_body=include_body)
    
    def head(self, kernel_name, path):
        self.get(kernel_name, path, include_body=False)


# URL to handler mappings

_kernel_name_regex = r"(?P<kernel_name>\w+)"

default_handlers = [
    (r"/api/kernelspecs", MainKernelSpecHandler),
    (r"/api/kernelspecs/%s" % _kernel_name_regex, KernelSpecHandler),
    (r"/api/kernelspecs/%s/(?P<path>.*)" % _kernel_name_regex, KernelSpecResourceHandler),
]
