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

import uuid
import sqlite3

from tornado import web

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import TraitError

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SessionManager(LoggingConfigurable):
    
    # Session database initialized below
    _cursor = None
    _connection = None
    
    @property
    def cursor(self):
        """Start a cursor and create a database called 'session'"""
        if self._cursor is None:
            self._cursor = self.connection.cursor()
            self._cursor.execute("""CREATE TABLE session 
                (id, name, path, kernel_id, ws_url)""")
        return self._cursor

    @property
    def connection(self):
        """Start a database connection"""
        if self._connection is None:
            self._connection = sqlite3.connect(':memory:')
            self._connection.row_factory = sqlite3.Row
        return self._connection
        
    def __del__(self):
        """Close connection once SessionManager closes"""
        self.cursor.close()

    def session_exists(self, name, path):
        """Check to see if the session for the given notebook exists"""
        self.cursor.execute("SELECT * FROM session WHERE name=? AND path=?", (name,path))
        reply = self.cursor.fetchone()
        if reply is None:
            return False
        else:
            return True

    def get_session_id(self):
        "Create a uuid for a new session"
        return unicode(uuid.uuid4())

    def create_session(self, name=None, path=None, kernel_id=None, ws_url=None):
        """Creates a session and returns its model"""
        session_id = self.get_session_id()
        return self.save_session(session_id, name=name, path=path, kernel_id=kernel_id, ws_url=ws_url)

    def save_session(self, session_id, name=None, path=None, kernel_id=None, ws_url=None):
        """Saves the items for the session with the given session_id
        
        Given a session_id (and any other of the arguments), this method
        creates a row in the sqlite session database that holds the information
        for a session.
        
        Parameters
        ----------
        session_id : str
            uuid for the session; this method must be given a session_id
        name : str
            the .ipynb notebook name that started the session
        path : str
            the path to the named notebook
        kernel_id : str
            a uuid for the kernel associated with this session
        ws_url : str
            the websocket url
            
        Returns
        -------
        model : dict
            a dictionary of the session model
        """
        self.cursor.execute("""INSERT INTO session VALUES 
            (?,?,?,?,?)""", (session_id, name, path, kernel_id, ws_url))
        self.connection.commit()
        return self.get_session(id=session_id)

    def get_session(self, **kwargs):
        """Returns the model for a particular session.
        
        Takes a keyword argument and searches for the value in the session
        database, then returns the rest of the session's info.

        Parameters
        ----------
        **kwargs : keyword argument
            must be given one of the keywords and values from the session database
            (i.e. session_id, name, path, kernel_id, ws_url)

        Returns
        -------
        model : dict
            returns a dictionary that includes all the information from the 
            session described by the kwarg.
        """
        column = kwargs.keys()[0] # uses only the first kwarg that is entered
        value = kwargs.values()[0]
        try:
            self.cursor.execute("SELECT * FROM session WHERE %s=?" %column, (value,))
        except sqlite3.OperationalError:
            raise TraitError("The session database has no column: %s" %column)
        reply = self.cursor.fetchone()
        if reply is not None:
            model = self.reply_to_dictionary_model(reply)
        else:
            raise web.HTTPError(404, u'Session not found: %s=%r' % (column, value))
        return model

    def update_session(self, session_id, **kwargs):
        """Updates the values in the session database.
        
        Changes the values of the session with the given session_id
        with the values from the keyword arguments. 
        
        Parameters
        ----------
        session_id : str
            a uuid that identifies a session in the sqlite3 database
        **kwargs : str
            the key must correspond to a column title in session database,
            and the value replaces the current value in the session 
            with session_id.
        """
        for kwarg in kwargs:
            try:
                self.cursor.execute("UPDATE session SET %s=? WHERE id=?" %kwarg, (kwargs[kwarg], session_id))
                self.connection.commit()
            except sqlite3.OperationalError:
                raise TraitError("No session exists with ID: %s" %session_id)

    def reply_to_dictionary_model(self, reply):
        """Takes sqlite database session row and turns it into a dictionary"""
        model = {'id': reply['id'],
                 'notebook': {'name': reply['name'], 'path': reply['path']},
                 'kernel': {'id': reply['kernel_id'], 'ws_url': reply['ws_url']}}
        return model
        
    def list_sessions(self):
        """Returns a list of dictionaries containing all the information from
        the session database"""
        session_list=[]
        self.cursor.execute("SELECT * FROM session")
        sessions = self.cursor.fetchall()
        for session in sessions:
            model = self.reply_to_dictionary_model(session)
            session_list.append(model)
        return session_list

    def delete_session(self, session_id):
        """Deletes the row in the session database with given session_id"""
        # Check that session exists before deleting
        model = self.get_session(id=session_id)
        self.cursor.execute("DELETE FROM session WHERE id=?", (session_id,))
        self.connection.commit()