"""Tornado handlers for the notebooks web service.

Authors:

* Zach Sailer
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from tornado import web

from zmq.utils import jsonapi

from IPython.utils.jsonutil import date_default

from ...base.handlers import IPythonHandler, authenticate_unless_readonly

#-----------------------------------------------------------------------------
# Session web service handlers
#-----------------------------------------------------------------------------



class SessionRootHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self):
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        sessions = sm.list_sessions()
        self.finish(jsonapi.dumps(sessions))

    @web.authenticated
    def post(self):
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        notebook_path = self.get_argument('notebook_path', default=None)
        notebook_name, path = nbm.named_notebook_path(notebook_path)
        session_id, model = sm.get_session(notebook_name, path)
        if model == None:
            kernel_id = km.start_kernel()
            kernel = km.kernel_model(kernel_id, self.ws_url)
            model = sm.session_model(session_id, notebook_name, path, kernel)
        self.finish(jsonapi.dumps(model))

class SessionHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'PATCH', 'DELETE')

    @authenticate_unless_readonly
    def get(self, session_id):
        sm = self.session_manager
        model = sm.get_session_from_id(session_id)
        self.finish(jsonapi.dumps(model))

    @web.authenticated
    def patch(self, session_id):
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        notebook_path = self.request.body
        notebook_name, path = nbm.named_notebook_path(notebook_path)
        kernel_id = sm.get_kernel_from_session(session_id)
        kernel = km.kernel_model(kernel_id, self.ws_url)
        sm.delete_mapping_for_session(session_id)
        model = sm.session_model(session_id, notebook_name, path, kernel)
        self.finish(jsonapi.dumps(model))

    @web.authenticated
    def delete(self, session_id):
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        kernel_id = sm.get_kernel_from_session(session_id)
        km.shutdown_kernel(kernel_id)
        sm.delete_mapping_for_session(session_id)
        self.set_status(204)
        self.finish()


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------

_session_id_regex = r"(?P<session_id>\w+-\w+-\w+-\w+-\w+)"

default_handlers = [
    (r"api/sessions/%s" % _session_id_regex, SessionHandler),
    (r"api/sessions",  SessionRootHandler)
]




