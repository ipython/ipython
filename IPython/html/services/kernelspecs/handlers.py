"""Tornado handlers for kernel specifications."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import json
from tornado import web

from ...base.handlers import IPythonHandler, json_errors

from IPython.kernel.kernelspec import _pythonfirst


class MainKernelSpecHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET',)

    @web.authenticated
    @json_errors
    def get(self):
        ksm = self.kernel_spec_manager
        results = []
        for kernel_name in sorted(ksm.find_kernel_specs(), key=_pythonfirst):
            try:
                d = ksm.get_kernel_spec(kernel_name).to_dict()
            except Exception:
                self.log.error("Failed to load kernel spec: '%s'", kernel_name, exc_info=True)
                continue
            d['name'] = kernel_name
            results.append(d)

        self.set_header("Content-Type", 'application/json')
        self.finish(json.dumps(results))


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


# URL to handler mappings

kernel_name_regex = r"(?P<kernel_name>\w+)"

default_handlers = [
    (r"/api/kernelspecs", MainKernelSpecHandler),
    (r"/api/kernelspecs/%s" % kernel_name_regex, KernelSpecHandler),
]
