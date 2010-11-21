"""A Task logger that presents our DB interface, 
but exists entirely in memory and implemented with dicts.

TaskRecords are dicts of the form:
{
    'msg_id' : str(uuid),
    'client_uuid' : str(uuid),
    'engine_uuid' : str(uuid) or None,
    'header' : dict(header),
    'content': dict(content),
    'buffers': list(buffers),
    'submitted': datetime,
    'started': datetime or None,
    'completed': datetime or None,
    'resubmitted': datetime or None,
    'result_header' : dict(header) or None,
    'result_content' : dict(content) or None,
    'result_buffers' : list(buffers) or None,
}
With this info, many of the special categories of tasks can be defined by query:

pending:  completed is None
client's outstanding: client_uuid = uuid && completed is None
MIA: arrived is None (and completed is None)
etc.

EngineRecords are dicts of the form:
{
    'eid' : int(id),
    'uuid': str(uuid)
}
This may be extended, but is currently.

We support a subset of mongodb operators:
    $lt,$gt,$lte,$gte,$ne,$in,$nin,$all,$mod,$exists
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------


from datetime import datetime

filters = {
 '$eq' : lambda a,b: a==b,
 '$lt' : lambda a,b: a < b,
 '$gt' : lambda a,b: b > a,
 '$lte': lambda a,b: a <= b,
 '$gte': lambda a,b: a >= b,
 '$ne' : lambda a,b: not a==b,
 '$in' : lambda a,b: a in b,
 '$nin': lambda a,b: a not in b,
 '$all' : lambda a,b: all([ a in bb for bb in b ]),
 '$mod': lambda a,b: a%b[0] == b[1],
 '$exists' : lambda a,b: (b and a is not None) or (a is None and not b)
}


class CompositeFilter(object):
    """Composite filter for matching multiple properties."""
    
    def __init__(self, dikt):
        self.tests = []
        self.values = []
        for key, value in dikt.iteritems():
            self.tests.append(filters[key])
            self.values.append(value)

    def __call__(self, value):
        for test,check in zip(self.tests, self.values):
            if not test(value, check):
                return False
        return True

class DictDB(object):
    """Basic in-memory dict-based object for saving Task Records.
    
    This is the first object to present the DB interface
    for logging tasks out of memory.
    
    The interface is based on MongoDB, so adding a MongoDB
    backend should be straightforward.
    """
    _records = None
    
    def __init__(self):
        self._records = dict()
    
    def _match_one(self, rec, tests):
        """Check if a specific record matches tests."""
        for key,test in tests.iteritems():
            if not test(rec.get(key, None)):
                return False
        return True
        
    def _match(self, check, id_only=True):
        """Find all the matches for a check dict."""
        matches = {}
        tests = {}
        for k,v in check.iteritems():
            if isinstance(v, dict):
                tests[k] = CompositeFilter(v)
            else:
                tests[k] = lambda o: o==v
        
        for msg_id, rec in self._records.iteritems():
            if self._match_one(rec, tests):
                matches[msg_id] = rec
        if id_only:
            return matches.keys()
        else:
            return matches
            
    
    def add_record(self, msg_id, rec):
        """Add a new Task Record, by msg_id."""
        if self._records.has_key(msg_id):
            raise KeyError("Already have msg_id %r"%(msg_id))
        self._records[msg_id] = rec
    
    def get_record(self, msg_id):
        """Get a specific Task Record, by msg_id."""
        if not self._records.has_key(msg_id):
            raise KeyError("No such msg_id %r"%(msg_id))
        return self._records[msg_id]
    
    def update_record(self, msg_id, rec):
        """Update the data in an existing record."""
        self._records[msg_id].update(rec)
    
    def drop_matching_records(self, check):
        """Remove a record from the DB."""
        matches = self._match(check, id_only=True)
        for m in matches:
            del self._records[m]
        
    def drop_record(self, msg_id):
        """Remove a record from the DB."""
        del self._records[msg_id]
        
    
    def find_records(self, check, id_only=False):
        """Find records matching a query dict."""
        matches = self._match(check, id_only)
        return matches