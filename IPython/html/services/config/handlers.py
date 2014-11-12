"""Tornado handlers for frontend config storage."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os
import io
import errno
from tornado import web

from IPython.utils.py3compat import PY3
from ...base.handlers import IPythonHandler, json_errors

def recursive_update(target, new):
    """Recursively update one dictionary using another.
    
    None values will delete their keys.
    """
    for k, v in new.items():
        if isinstance(v, dict):
            if k not in target:
                target[k] = {}
            recursive_update(target[k], v)
            if not target[k]:
                # Prune empty subdicts
                del target[k]

        elif v is None:
            target.pop(k, None)

        else:
            target[k] = v

class ConfigHandler(IPythonHandler):
    SUPPORTED_METHODS = ('GET', 'PUT', 'PATCH')

    @property
    def config_dir(self):
        return os.path.join(self.profile_dir, 'nbconfig')

    def ensure_config_dir_exists(self):
        try:
            os.mkdir(self.config_dir, 0o755)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def file_name(self, section_name):
        return os.path.join(self.config_dir, section_name+'.json')

    @web.authenticated
    @json_errors
    def get(self, section_name):
        self.set_header("Content-Type", 'application/json')
        filename = self.file_name(section_name)
        if os.path.isfile(filename):
            with io.open(filename, encoding='utf-8') as f:
                self.finish(f.read())
        else:
            self.finish("{}")

    @web.authenticated
    @json_errors
    def put(self, section_name):
        self.get_json_body()  # Will raise 400 if content is not valid JSON
        filename = self.file_name(section_name)
        self.ensure_config_dir_exists()
        with open(filename, 'wb') as f:
            f.write(self.request.body)
        self.set_status(204)

    @web.authenticated
    @json_errors
    def patch(self, section_name):
        filename = self.file_name(section_name)
        if os.path.isfile(filename):
            with io.open(filename, encoding='utf-8') as f:
                section = json.load(f)
        else:
            section = {}

        update = self.get_json_body()
        recursive_update(section, update)

        self.ensure_config_dir_exists()
        if PY3:
            f = io.open(filename, 'w', encoding='utf-8')
        else:
            f = open(filename, 'wb')
        with f:
            json.dump(section, f)

        self.finish(json.dumps(section))


# URL to handler mappings

section_name_regex = r"(?P<section_name>\w+)"

default_handlers = [
    (r"/api/config/%s" % section_name_regex, ConfigHandler),
]
