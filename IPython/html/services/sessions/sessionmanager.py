"""A base class session manager."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import uuid
import sqlite3

from tornado import web

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.py3compat import unicode_type
from IPython.utils.traitlets import Instance


class SessionManager(LoggingConfigurable):

    kernel_manager = Instance('IPython.html.services.kernels.kernelmanager.MappingKernelManager')
    contents_manager = Instance('IPython.html.services.contents.manager.ContentsManager')
    
    # Session database initialized below
    _cursor = None
    _connection = None
    _columns = {'session_id', 'path', 'kernel_id'}
    
    @property
    def cursor(self):
        """Start a cursor and create a database called 'session'"""
        if self._cursor is None:
            self._cursor = self.connection.cursor()
            self._cursor.execute("""CREATE TABLE session 
                (session_id, path, kernel_id)""")
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

    def session_exists(self, path):
        """Check to see if the session for a given notebook exists"""
        self.cursor.execute("SELECT * FROM session WHERE path=?", (path,))
        reply = self.cursor.fetchone()
        if reply is None:
            return False
        else:
            return True

    def new_session_id(self):
        "Create a uuid for a new session"
        return unicode_type(uuid.uuid4())

    def create_session(self, path=None, kernel_name=None):
        """Creates a session and returns its model"""
        session_id = self.new_session_id()
        # allow nbm to specify kernels cwd
        kernel_path = self.contents_manager.get_kernel_path(path=path)
        kernel_id = self.kernel_manager.start_kernel(path=kernel_path,
                                                     kernel_name=kernel_name)
        return self.save_session(session_id, path=path,
                                 kernel_id=kernel_id)

    def save_session(self, session_id, path=None, kernel_id=None):
        """Saves the items for the session with the given session_id
        
        Given a session_id (and any other of the arguments), this method
        creates a row in the sqlite session database that holds the information
        for a session.
        
        Parameters
        ----------
        session_id : str
            uuid for the session; this method must be given a session_id
        path : str
            the path for the given notebook
        kernel_id : str
            a uuid for the kernel associated with this session
        
        Returns
        -------
        model : dict
            a dictionary of the session model
        """
        self.cursor.execute("INSERT INTO session VALUES (?,?,?)",
            (session_id, path, kernel_id)
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
            (i.e. session_id, path, kernel_id)

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
        try:
            row = self.cursor.fetchone()
        except KeyError:
            # The kernel is missing, so the session just got deleted.
            row = None

        if row is None:
            q = []
            for key, value in kwargs.items():
                q.append("%s=%r" % (key, value))

            raise web.HTTPError(404, u'Session not found: %s' % (', '.join(q)))

        return self.row_to_model(row)

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

    def row_to_model(self, row):
        """Takes sqlite database session row and turns it into a dictionary"""
        if row['kernel_id'] not in self.kernel_manager:
            # The kernel was killed or died without deleting the session.
            # We can't use delete_session here because that tries to find
            # and shut down the kernel.
            self.cursor.execute("DELETE FROM session WHERE session_id=?", 
                                (row['session_id'],))
            raise KeyError

        model = {
            'id': row['session_id'],
            'notebook': {
                'path': row['path']
            },
            'kernel': self.kernel_manager.kernel_model(row['kernel_id'])
        }
        return model

    def list_sessions(self):
        """Returns a list of dictionaries containing all the information from
        the session database"""
        c = self.cursor.execute("SELECT * FROM session")
        result = []
        # We need to use fetchall() here, because row_to_model can delete rows,
        # which messes up the cursor if we're iterating over rows.
        for row in c.fetchall():
            try:
                result.append(self.row_to_model(row))
            except KeyError:
                pass
        return result

    def delete_session(self, session_id):
        """Deletes the row in the session database with given session_id"""
        # Check that session exists before deleting
        session = self.get_session(session_id=session_id)
        self.kernel_manager.shutdown_kernel(session['kernel']['id'])
        self.cursor.execute("DELETE FROM session WHERE session_id=?", (session_id,))
