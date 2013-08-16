"""A TaskRecord backend using mongodb

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from pymongo import Connection

# bson.Binary import moved
try:
    from bson.binary import Binary
except ImportError:
    from bson import Binary

from IPython.utils.traitlets import Dict, List, Unicode, Instance

from .dictdb import BaseDB

#-----------------------------------------------------------------------------
# MongoDB class
#-----------------------------------------------------------------------------

class MongoDB(BaseDB):
    """MongoDB TaskRecord backend."""
    
    connection_args = List(config=True,
        help="""Positional arguments to be passed to pymongo.Connection.  Only
        necessary if the default mongodb configuration does not point to your
        mongod instance.""")
    connection_kwargs = Dict(config=True,
        help="""Keyword arguments to be passed to pymongo.Connection.  Only
        necessary if the default mongodb configuration does not point to your
        mongod instance."""
    )
    database = Unicode(config=True,
        help="""The MongoDB database name to use for storing tasks for this session. If unspecified,
        a new database will be created with the Hub's IDENT.  Specifying the database will result
        in tasks from previous sessions being available via Clients' db_query and
        get_result methods.""")

    _connection = Instance(Connection) # pymongo connection
    
    def __init__(self, **kwargs):
        super(MongoDB, self).__init__(**kwargs)
        if self._connection is None:
            self._connection = Connection(*self.connection_args, **self.connection_kwargs)
        if not self.database:
            self.database = self.session
        self._db = self._connection[self.database]
        self._records = self._db['task_records']
        self._records.ensure_index('msg_id', unique=True)
        self._records.ensure_index('submitted') # for sorting history
        # for rec in self._records.find
    
    def _binary_buffers(self, rec):
        for key in ('buffers', 'result_buffers'):
            if rec.get(key, None):
                rec[key] = map(Binary, rec[key])
        return rec
    
    def add_record(self, msg_id, rec):
        """Add a new Task Record, by msg_id."""
        # print rec
        rec = self._binary_buffers(rec)
        self._records.insert(rec)
    
    def get_record(self, msg_id):
        """Get a specific Task Record, by msg_id."""
        r = self._records.find_one({'msg_id': msg_id})
        if not r:
            # r will be '' if nothing is found
            raise KeyError(msg_id)
        return r
    
    def update_record(self, msg_id, rec):
        """Update the data in an existing record."""
        rec = self._binary_buffers(rec)

        self._records.update({'msg_id':msg_id}, {'$set': rec})
    
    def drop_matching_records(self, check):
        """Remove a record from the DB."""
        self._records.remove(check)
        
    def drop_record(self, msg_id):
        """Remove a record from the DB."""
        self._records.remove({'msg_id':msg_id})
    
    def find_records(self, check, keys=None):
        """Find records matching a query dict, optionally extracting subset of keys.
        
        Returns list of matching records.
        
        Parameters
        ----------
        
        check: dict
            mongodb-style query argument
        keys: list of strs [optional]
            if specified, the subset of keys to extract.  msg_id will *always* be
            included.
        """
        if keys and 'msg_id' not in keys:
            keys.append('msg_id')
        matches = list(self._records.find(check,keys))
        for rec in matches:
            rec.pop('_id')
        return matches

    def get_history(self):
        """get all msg_ids, ordered by time submitted."""
        cursor = self._records.find({},{'msg_id':1}).sort('submitted')
        return [ rec['msg_id'] for rec in cursor ]


