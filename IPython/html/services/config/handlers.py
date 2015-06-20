"""Tornado handlers for frontend config storage."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os
import io
import errno
from tornado import web

from IPython.utils.py3compat import PY3
from ...base.handlers import APIHandler, json_errors

class ConfigHandler(APIHandler):
    SUPPORTED_METHODS = ('GET', 'PUT', 'PATCH')

    @web.authenticated
    @json_errors
    def get(self, section_name):
        self.set_header("Content-Type", 'application/json')
        self.finish(json.dumps(self.config_manager.get(section_name)))

    @web.authenticated
    @json_errors
    def put(self, section_name):
        data = self.get_json_body()  # Will raise 400 if content is not valid JSON
        self.config_manager.set(section_name, data)
        self.set_status(204)

    @web.authenticated
    @json_errors
    def patch(self, section_name):
        new_data = self.get_json_body()
        section = self.config_manager.update(section_name, new_data)
        self.finish(json.dumps(section))


# URL to handler mappings

section_name_regex = r"(?P<section_name>\w+)"

default_handlers = [
    (r"/api/config/%s" % section_name_regex, ConfigHandler),
]
