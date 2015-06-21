"""Tornado handlers for the sessions web service."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json

from tornado import web

from ...base.handlers import APIHandler, json_errors
from IPython.utils.jsonutil import date_default
from IPython.html.utils import url_path_join, url_escape
from IPython.kernel.kernelspec import NoSuchKernel


class SessionRootHandler(APIHandler):

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
        cm = self.contents_manager
        km = self.kernel_manager

        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, "No JSON data provided")
        try:
            path = model['notebook']['path']
        except KeyError:
            raise web.HTTPError(400, "Missing field in JSON data: notebook.path")
        try:
            kernel_name = model['kernel']['name']
        except KeyError:
            self.log.debug("No kernel name specified, using default kernel")
            kernel_name = None

        # Check to see if session exists
        if sm.session_exists(path=path):
            model = sm.get_session(path=path)
        else:
            try:
                model = sm.create_session(path=path, kernel_name=kernel_name)
            except NoSuchKernel:
                msg = ("The '%s' kernel is not available. Please pick another "
                       "suitable kernel instead, or install that kernel." % kernel_name)
                status_msg = '%s not found' % kernel_name
                self.log.warn('Kernel not found: %s' % kernel_name)
                self.set_status(501)
                self.finish(json.dumps(dict(message=msg, short_message=status_msg)))
                return

        location = url_path_join(self.base_url, 'api', 'sessions', model['id'])
        self.set_header('Location', url_escape(location))
        self.set_status(201)
        self.finish(json.dumps(model, default=date_default))

class SessionHandler(APIHandler):

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
        try:
            sm.delete_session(session_id)
        except KeyError:
            # the kernel was deleted but the session wasn't!
            raise web.HTTPError(410, "Kernel deleted before session")
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

