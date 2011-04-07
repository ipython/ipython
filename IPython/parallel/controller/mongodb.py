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
    
    connection_args = List(config=True)
    connection_kwargs = Dict(config=True)
    database = CUnicode(config=True)
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
            if key in rec:
                rec[key] = map(Binary, rec[key])
    
    def add_record(self, msg_id, rec):
        """Add a new Task Record, by msg_id."""
        # print rec
        rec = _binary_buffers(rec)
        obj_id = self._records.insert(rec)
        self._table[msg_id] = obj_id
    
    def get_record(self, msg_id):
        """Get a specific Task Record, by msg_id."""
        return self._records.find_one(self._table[msg_id])
    
    def update_record(self, msg_id, rec):
        """Update the data in an existing record."""
        rec = _binary_buffers(rec)
        obj_id = self._table[msg_id]
        self._records.update({'_id':obj_id}, {'$set': rec})
    
    def drop_matching_records(self, check):
        """Remove a record from the DB."""
        self._records.remove(check)
        
    def drop_record(self, msg_id):
        """Remove a record from the DB."""
        obj_id = self._table.pop(msg_id)
        self._records.remove(obj_id)
    
    def find_records(self, check, id_only=False):
        """Find records matching a query dict."""
        matches = list(self._records.find(check))
        if id_only:
            return [ rec['msg_id'] for rec in matches ]
        else:
            data = {}
            for rec in matches:
                data[rec['msg_id']] = rec
            return data


