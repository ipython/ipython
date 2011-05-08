"""A TaskRecord backend using mongodb"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from datetime import datetime

from pymongo import Connection
from pymongo.binary import Binary

from IPython.utils.traitlets import Dict, List, CUnicode

from .dictdb import BaseDB

#-----------------------------------------------------------------------------
# MongoDB class
#-----------------------------------------------------------------------------

class MongoDB(BaseDB):
    """MongoDB TaskRecord backend."""
    
    connection_args = List(config=True) # args passed to pymongo.Connection
    connection_kwargs = Dict(config=True) # kwargs passed to pymongo.Connection
    database = CUnicode(config=True) # name of the mongodb database
    _table = Dict()
    
    def __init__(self, **kwargs):
        super(MongoDB, self).__init__(**kwargs)
        self._connection = Connection(*self.connection_args, **self.connection_kwargs)
        if not self.database:
            self.database = self.session
        self._db = self._connection[self.database]
        self._records = self._db['task_records']
    
    def _binary_buffers(self, rec):
        for key in ('buffers', 'result_buffers'):
            if rec.get(key, None):
                rec[key] = map(Binary, rec[key])
        return rec
    
    def add_record(self, msg_id, rec):
        """Add a new Task Record, by msg_id."""
        # print rec
        rec = self._binary_buffers(rec)
        obj_id = self._records.insert(rec)
        self._table[msg_id] = obj_id
    
    def get_record(self, msg_id):
        """Get a specific Task Record, by msg_id."""
        return self._records.find_one(self._table[msg_id])
    
    def update_record(self, msg_id, rec):
        """Update the data in an existing record."""
        rec = self._binary_buffers(rec)
        obj_id = self._table[msg_id]
        self._records.update({'_id':obj_id}, {'$set': rec})
    
    def drop_matching_records(self, check):
        """Remove a record from the DB."""
        self._records.remove(check)
        
    def drop_record(self, msg_id):
        """Remove a record from the DB."""
        obj_id = self._table.pop(msg_id)
        self._records.remove(obj_id)
    
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


