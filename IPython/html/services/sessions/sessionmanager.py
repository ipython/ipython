"""A base class session manager.

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

import os
import uuid

from tornado import web

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current
from IPython.utils.traitlets import List, Dict, Unicode, TraitError

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SessionManager(LoggingConfigurable):
    
    # Use session_ids to map notebook names to kernel_ids
    sessions = List()
    
    def get_session(self, nb_name, nb_path=None):
        """Get an existing session or create a new one"""
        model = None
        for session in self.sessions:
            if session['name'] == nb_name and session['path'] == nb_path:
                session_id = session['id']
                model = session
        if model != None:
            return session_id, model
        else:
            session_id = unicode(uuid.uuid4())
            return session_id, model
    
    def session_model(self, session_id, notebook_name=None, notebook_path=None, kernel=None):
        """ Create a session that links notebooks with kernels """
        model = dict(id=session_id,
                name=notebook_name, 
                path=notebook_path, 
                kernel=kernel)
        if notebook_path == None:
            model['path']=""
        self.sessions.append(model)
        return model
    
    def list_sessions(self):
        """List all sessions and their information"""
        return self.sessions
    
    def set_kernel_for_sessions(self, session_id, kernel_id):
        """Maps the kernel_ids to the session_id in session_mapping"""
        for session in self.sessions:
            if session['id'] == session_id:
                session['kernel']['id'] = kernel_id
        return self.sessions
        
    def delete_mapping_for_session(self, session_id):
        """Delete the session from session_mapping with the given session_id"""
        i = 0
        for session in self.sessions:
            if session['id'] == session_id:
                del self.sessions[i]
            i = i + 1
        return self.sessions
        
    def get_session_from_id(self, session_id):
        for session in self.sessions:
            if session['id'] == session_id:
                return session

    def get_notebook_from_session(self, session_id):
        """Returns the notebook_path for the given session_id"""
        for session in self.sessions:
            if session['id'] == session_id:
                return session['name']
    
    def get_kernel_from_session(self, session_id):
        """Returns the kernel_id for the given session_id"""
        for session in self.sessions:
            if session['id'] == session_id:
                return session['kernel']['id']
        
