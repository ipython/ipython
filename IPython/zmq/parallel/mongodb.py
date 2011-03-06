"""A TaskRecord backend using mongodb"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from datetime import datetime

from pymongo import Connection

from .dictdb import BaseDB

#-----------------------------------------------------------------------------
# MongoDB class
#-----------------------------------------------------------------------------

class MongoDB(BaseDB):
    """MongoDB TaskRecord backend."""
    def __init__(self, session_uuid, *args, **kwargs):
        self._connection = Connection(*args, **kwargs)
        self._db = self._connection[session_uuid]
        self._records = self._db['task_records']
        self._table = {}
    
    def add_record(self, msg_id, rec):
        """Add a new Task Record, by msg_id."""
        # print rec
        obj_id = self._records.insert(rec)
        self._table[msg_id] = obj_id
    
    def get_record(self, msg_id):
        """Get a specific Task Record, by msg_id."""
        return self._records.find_one(self._table[msg_id])
    
    def update_record(self, msg_id, rec):
        """Update the data in an existing record."""
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


