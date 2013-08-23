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

from tornado import web

from zmq.utils import jsonapi

from IPython.utils.jsonutil import date_default
from ...base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# Session web service handlers
#-----------------------------------------------------------------------------


class SessionRootHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        # Return a list of running sessions
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        sessions = sm.list_sessions()
        self.finish(jsonapi.dumps(sessions))

    @web.authenticated
    def post(self):
        # Creates a new session 
        #(unless a session already exists for the named nb)
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        notebook_path = self.get_argument('notebook_path', default=None)
        name, path = nbm.named_notebook_path(notebook_path)
        # Check to see if session exists
        if sm.session_exists(name=name, path=path):
            model = sm.get_session(name=name, path=path)
            kernel_id = model['kernel']['id']
            km.start_kernel(kernel_id, cwd=nbm.notebook_dir)
        else:
            session_id = sm.get_session_id()
            sm.save_session(session_id=session_id, name=name, path=path)
            kernel_id = km.start_kernel(cwd=nbm.notebook_dir)
            kernel = km.kernel_model(kernel_id, self.ws_url)
            sm.update_session(session_id, kernel=kernel_id)
            model = sm.get_session(id=session_id)
        self.set_header('Location', '{0}kernels/{1}'.format(self.base_kernel_url, kernel_id))
        self.finish(jsonapi.dumps(model))

class SessionHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'PATCH', 'DELETE')

    @web.authenticated
    def get(self, session_id):
        # Returns the JSON model for a single session
        sm = self.session_manager
        model = sm.get_session(id=session_id)
        self.finish(jsonapi.dumps(model))

    @web.authenticated
    def patch(self, session_id):
        # Currently, this handler is strictly for renaming notebooks
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        data = jsonapi.loads(self.request.body)
        name, path = nbm.named_notebook_path(data['notebook_path'])
        sm.update_session(session_id, name=name)
        model = sm.get_session(id=session_id)
        self.finish(jsonapi.dumps(model))

    @web.authenticated
    def delete(self, session_id):
        # Deletes the session with given session_id
        sm = self.session_manager
        nbm = self.notebook_manager
        km = self.kernel_manager
        session = sm.get_session(id=session_id)
        sm.delete_session(session_id)        
        km.shutdown_kernel(session['kernel']['id'])
        self.set_status(204)
        self.finish()


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------

_session_id_regex = r"(?P<session_id>\w+-\w+-\w+-\w+-\w+)"

default_handlers = [
    (r"api/sessions/%s/" % _session_id_regex, SessionHandler),
    (r"api/sessions/%s" % _session_id_regex, SessionHandler),
    (r"api/sessions/",  SessionRootHandler),
    (r"api/sessions",  SessionRootHandler)
]

