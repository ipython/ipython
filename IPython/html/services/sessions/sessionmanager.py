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
from IPython.utils.py3compat import unicode_type

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SessionManager(LoggingConfigurable):
    
    # Session database initialized below
    _cursor = None
    _connection = None
    _columns = {'session_id', 'name', 'path', 'kernel_id'}
    
    @property
    def cursor(self):
        """Start a cursor and create a database called 'session'"""
        if self._cursor is None:
            self._cursor = self.connection.cursor()
            self._cursor.execute("""CREATE TABLE session 
                (session_id, name, path, kernel_id)""")
        return self._cursor

    @property
    def connection(self):
        """Start a database connection"""
        if self._connection is None:
            self._connection = sqlite3.connect(':memory:')
            self._connection.row_factory = self.row_factory
        return self._connection
        
    def __del__(self):
        """Close connection once SessionManager closes"""
        self.cursor.close()

    def session_exists(self, name, path):
        """Check to see if the session for a given notebook exists"""
        self.cursor.execute("SELECT * FROM session WHERE name=? AND path=?", (name, path))
        reply = self.cursor.fetchone()
        if reply is None:
            return False
        else:
            return True

    def new_session_id(self):
        "Create a uuid for a new session"
        return unicode_type(uuid.uuid4())

    def create_session(self, name=None, path=None, kernel_id=None):
        """Creates a session and returns its model"""
        session_id = self.new_session_id()
        return self.save_session(session_id, name=name, path=path, kernel_id=kernel_id)

    def save_session(self, session_id, name=None, path=None, kernel_id=None):
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
        
        Returns
        -------
        model : dict
            a dictionary of the session model
        """
        self.cursor.execute("INSERT INTO session VALUES (?,?,?,?)",
            (session_id, name, path, kernel_id)
        )
        return self.get_session(session_id=session_id)

    def get_session(self, **kwargs):
        """Returns the model for a particular session.
        
        Takes a keyword argument and searches for the value in the session
        database, then returns the rest of the session's info.

        Parameters
        ----------
        **kwargs : keyword argument
            must be given one of the keywords and values from the session database
            (i.e. session_id, name, path, kernel_id)

        Returns
        -------
        model : dict
            returns a dictionary that includes all the information from the 
            session described by the kwarg.
        """
        if not kwargs:
            raise TypeError("must specify a column to query")

        conditions = []
        for column in kwargs.keys():
            if column not in self._columns:
                raise TypeError("No such column: %r", column)
            conditions.append("%s=?" % column)

        query = "SELECT * FROM session WHERE %s" % (' AND '.join(conditions))

        self.cursor.execute(query, list(kwargs.values()))
        model = self.cursor.fetchone()
        if model is None:
            q = []
            for key, value in kwargs.items():
                q.append("%s=%r" % (key, value))

            raise web.HTTPError(404, u'Session not found: %s' % (', '.join(q)))
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
        self.get_session(session_id=session_id)

        if not kwargs:
            # no changes
            return

        sets = []
        for column in kwargs.keys():
            if column not in self._columns:
                raise TypeError("No such column: %r" % column)
            sets.append("%s=?" % column)
        query = "UPDATE session SET %s WHERE session_id=?" % (', '.join(sets))
        self.cursor.execute(query, list(kwargs.values()) + [session_id])

    @staticmethod
    def row_factory(cursor, row):
        """Takes sqlite database session row and turns it into a dictionary"""
        row = sqlite3.Row(cursor, row)
        model = {
            'id': row['session_id'],
            'notebook': {
                'name': row['name'],
                'path': row['path']
            },
            'kernel': {
                'id': row['kernel_id'],
            }
        }
        return model

    def list_sessions(self):
        """Returns a list of dictionaries containing all the information from
        the session database"""
        c = self.cursor.execute("SELECT * FROM session")
        return list(c.fetchall())

    def delete_session(self, session_id):
        """Deletes the row in the session database with given session_id"""
        # Check that session exists before deleting
        self.get_session(session_id=session_id)
        self.cursor.execute("DELETE FROM session WHERE session_id=?", (session_id,))
