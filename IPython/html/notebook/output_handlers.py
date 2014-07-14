"""Tornado handlers for the output iframes for the live notebook view.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
from tornado import web
HTTPError = web.HTTPError

from ..base.handlers import IPythonHandler, notebook_path_regex, path_regex
from ..utils import url_path_join, url_escape


class OutputAreaHandler(IPythonHandler):
    @web.authenticated
    def get(self, path='', name=None):
        """Renders the output iframe template."""
        self.write(self.render_template('framecontents.html',
            mathjax_url=self.mathjax_url
            framerequire = 'notebook/js/outputarea.js'
            frameid = 'outputarea'))


class WidgetAreaHandler(IPythonHandler):
    @web.authenticated
    def get(self, path='', name=None):
        """Renders the widgetarea iframe template."""
        self.write(self.render_template('framecontents.html',
            mathjax_url=self.mathjax_url
            framerequire = 'widgets/js/frame.js'
            frameid = 'widgetarea'))


class WidgetManagerHandler(IPythonHandler):
    @web.authenticated
    def get(self, path='', name=None):
        """Renders the widgetmanager iframe template."""
        self.write(self.render_template('framecontents.html',
            mathjax_url=self.mathjax_url
            framerequire = 'widgets/js/manager_frame.js'
            frameid = 'widgetmanager'))


default_handlers = [
    (r"/outputarea", OutputAreaHandler),
    (r"/widgetarea", WidgetAreaHandler),
    (r"/widgetmanager", WidgetManagerHandler),
]
