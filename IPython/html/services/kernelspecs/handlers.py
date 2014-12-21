"""Tornado handlers for kernel specifications."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import glob
import json
import os
pjoin = os.path.join

from tornado import web

from ...base.handlers import IPythonHandler, json_errors
from ...utils import url_path_join

def kernelspec_model(handler, name):
    """Load a KernelSpec by name and return the REST API model"""
    ksm = handler.kernel_spec_manager
    spec = ksm.get_kernel_spec(name)
    d = {'name': name}
    d['spec'] = spec.to_dict()
    d['resources'] = resources = {}
    resource_dir = spec.resource_dir
    for resource in ['kernel.js', 'kernel.css']:
        if os.path.exists(pjoin(resource_dir, resource)):
            resources[resource] = url_path_join(
                handler.base_url,
                'kernelspecs',
                name,
                resource
            )
    for logo_file in glob.glob(pjoin(resource_dir, 'logo-*')):
        fname = os.path.basename(logo_file)
        no_ext, _ = os.path.splitext(fname)
        resources[no_ext] = url_path_join(
            handler.base_url,
            'kernelspecs',
            name,
            fname
        )
    return d

class MainKernelSpecHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET',)

    @web.authenticated
    @json_errors
    def get(self):
        ksm = self.kernel_spec_manager
        km = self.kernel_manager
        model = {}
        model['default'] = km.default_kernel_name
        model['kernelspecs'] = specs = {}
        for kernel_name in ksm.find_kernel_specs():
            try:
                d = kernelspec_model(self, kernel_name)
            except Exception:
                self.log.error("Failed to load kernel spec: '%s'", kernel_name, exc_info=True)
                continue
            specs[kernel_name] = d
        self.set_header("Content-Type", 'application/json')
        self.finish(json.dumps(model))


class KernelSpecHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET',)

    @web.authenticated
    @json_errors
    def get(self, kernel_name):
        try:
            model = kernelspec_model(self, kernel_name)
        except KeyError:
            raise web.HTTPError(404, u'Kernel spec %s not found' % kernel_name)
        self.set_header("Content-Type", 'application/json')
        self.finish(json.dumps(model))


# URL to handler mappings

kernel_name_regex = r"(?P<kernel_name>\w+)"

default_handlers = [
    (r"/api/kernelspecs", MainKernelSpecHandler),
    (r"/api/kernelspecs/%s" % kernel_name_regex, KernelSpecHandler),
]
