"""Tornado handlers for the sessions web service.

Authors:

* Zach Sailer
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import json

from tornado import web

from ...base.handlers import IPythonHandler, json_errors
from IPython.utils.jsonutil import date_default
from IPython.html.utils import url_path_join, url_escape

#-----------------------------------------------------------------------------
# Session web service handlers
#-----------------------------------------------------------------------------


class SessionRootHandler(IPythonHandler):

    @web.authenticated
    @json_errors
    def get(self):
        # Return a list of running sessions
        sm = self.session_manager
        sessions = sm.list_sessions()
        self.finish(json.dumps(sessions, default=date_default))

    @web.authenticated
    @json_errors
    def post(self):
        # Creates a new session 
        #(unless a session already exists for the named nb)
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, "No JSON data provided")
        try:
            name = model['notebook']['name']
        except KeyError:
            raise web.HTTPError(400, "Missing field in JSON data: name")
        try:
            path = model['notebook']['path']
        except KeyError:
            raise web.HTTPError(400, "Missing field in JSON data: path")
        # Check to see if session exists
        if sm.session_exists(name=name, path=path):
            model = sm.get_session(name=name, path=path)
        else:
            kernel_id = km.start_kernel(path=path)
            model = sm.create_session(name=name, path=path, kernel_id=kernel_id)
        location = url_path_join(self.base_url, 'api', 'sessions', model['id'])
        self.set_header('Location', url_escape(location))
        self.set_status(201)
        self.finish(json.dumps(model, default=date_default))

class SessionHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'PATCH', 'DELETE')

    @web.authenticated
    @json_errors
    def get(self, session_id):
        # Returns the JSON model for a single session
        sm = self.session_manager
        model = sm.get_session(session_id=session_id)
        self.finish(json.dumps(model, default=date_default))

    @web.authenticated
    @json_errors
    def patch(self, session_id):
        # Currently, this handler is strictly for renaming notebooks
        sm = self.session_manager
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, "No JSON data provided")
        changes = {}
        if 'notebook' in model:
            notebook = model['notebook']
            if 'name' in notebook:
                changes['name'] = notebook['name']
            if 'path' in notebook:
                changes['path'] = notebook['path']

        sm.update_session(session_id, **changes)
        model = sm.get_session(session_id=session_id)
        self.finish(json.dumps(model, default=date_default))

    @web.authenticated
    @json_errors
    def delete(self, session_id):
        # Deletes the session with given session_id
        sm = self.session_manager
        km = self.kernel_manager
        session = sm.get_session(session_id=session_id)
        sm.delete_session(session_id)
        km.shutdown_kernel(session['kernel']['id'])
        self.set_status(204)
        self.finish()


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------

_session_id_regex = r"(?P<session_id>\w+-\w+-\w+-\w+-\w+)"

default_handlers = [
    (r"/api/sessions/%s" % _session_id_regex, SessionHandler),
    (r"/api/sessions",  SessionRootHandler)
]

