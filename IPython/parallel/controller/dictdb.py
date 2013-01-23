"""A Task logger that presents our DB interface,
but exists entirely in memory and implemented with dicts.

Authors:

* Min RK


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
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from copy import deepcopy as copy
from datetime import datetime

from IPython.config.configurable import LoggingConfigurable

from IPython.utils.traitlets import Dict, Unicode, Integer, Float

filters = {
 '$lt' : lambda a,b: a < b,
 '$gt' : lambda a,b: b > a,
 '$eq' : lambda a,b: a == b,
 '$ne' : lambda a,b: a != b,
 '$lte': lambda a,b: a <= b,
 '$gte': lambda a,b: a >= b,
 '$in' : lambda a,b: a in b,
 '$nin': lambda a,b: a not in b,
 '$all': lambda a,b: all([ a in bb for bb in b ]),
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

class BaseDB(LoggingConfigurable):
    """Empty Parent class so traitlets work on DB."""
    # base configurable traits:
    session = Unicode("")

class DictDB(BaseDB):
    """Basic in-memory dict-based object for saving Task Records.

    This is the first object to present the DB interface
    for logging tasks out of memory.

    The interface is based on MongoDB, so adding a MongoDB
    backend should be straightforward.
    """

    _records = Dict()
    _culled_ids = set() # set of ids which have been culled
    _buffer_bytes = Integer(0) # running total of the bytes in the DB
    
    size_limit = Integer(1024*1024, config=True,
        help="""The maximum total size (in bytes) of the buffers stored in the db
        
        When the db exceeds this size, the oldest records will be culled until
        the total size is under size_limit * (1-cull_fraction).
        """
    )
    record_limit = Integer(1024, config=True,
        help="""The maximum number of records in the db
        
        When the history exceeds this size, the first record_limit * cull_fraction
        records will be culled.
        """
    )
    cull_fraction = Float(0.1, config=True,
        help="""The fraction by which the db should culled when one of the limits is exceeded
        
        In general, the db size will spend most of its time with a size in the range:
        
        [limit * (1-cull_fraction), limit]
        
        for each of size_limit and record_limit.
        """
    )

    def _match_one(self, rec, tests):
        """Check if a specific record matches tests."""
        for key,test in tests.iteritems():
            if not test(rec.get(key, None)):
                return False
        return True

    def _match(self, check):
        """Find all the matches for a check dict."""
        matches = []
        tests = {}
        for k,v in check.iteritems():
            if isinstance(v, dict):
                tests[k] = CompositeFilter(v)
            else:
                tests[k] = lambda o: o==v

        for rec in self._records.itervalues():
            if self._match_one(rec, tests):
                matches.append(copy(rec))
        return matches

    def _extract_subdict(self, rec, keys):
        """extract subdict of keys"""
        d = {}
        d['msg_id'] = rec['msg_id']
        for key in keys:
            d[key] = rec[key]
        return copy(d)
    
    # methods for monitoring size / culling history
    
    def _add_bytes(self, rec):
        for key in ('buffers', 'result_buffers'):
            for buf in rec.get(key) or []:
                self._buffer_bytes += len(buf)
        
        self._maybe_cull()
    
    def _drop_bytes(self, rec):
        for key in ('buffers', 'result_buffers'):
            for buf in rec.get(key) or []:
                self._buffer_bytes -= len(buf)
    
    def _cull_oldest(self, n=1):
        """cull the oldest N records"""
        for msg_id in self.get_history()[:n]:
            self.log.debug("Culling record: %r", msg_id)
            self._culled_ids.add(msg_id)
            self.drop_record(msg_id)
    
    def _maybe_cull(self):
        # cull by count:
        if len(self._records) > self.record_limit:
            to_cull = int(self.cull_fraction * self.record_limit)
            self.log.info("%i records exceeds limit of %i, culling oldest %i",
                len(self._records), self.record_limit, to_cull
            )
            self._cull_oldest(to_cull)
        
        # cull by size:
        if self._buffer_bytes > self.size_limit:
            limit = self.size_limit * (1 - self.cull_fraction)
            
            before = self._buffer_bytes
            before_count = len(self._records)
            culled = 0
            while self._buffer_bytes > limit:
                self._cull_oldest(1)
                culled += 1
        
            self.log.info("%i records with total buffer size %i exceeds limit: %i. Culled oldest %i records.",
                before_count, before, self.size_limit, culled
            )
    
    # public API methods:

    def add_record(self, msg_id, rec):
        """Add a new Task Record, by msg_id."""
        if msg_id in self._records:
            raise KeyError("Already have msg_id %r"%(msg_id))
        self._records[msg_id] = rec
        self._add_bytes(rec)
        self._maybe_cull()

    def get_record(self, msg_id):
        """Get a specific Task Record, by msg_id."""
        if msg_id in self._culled_ids:
            raise KeyError("Record %r has been culled for size" % msg_id)
        if not msg_id in self._records:
            raise KeyError("No such msg_id %r"%(msg_id))
        return copy(self._records[msg_id])

    def update_record(self, msg_id, rec):
        """Update the data in an existing record."""
        if msg_id in self._culled_ids:
            raise KeyError("Record %r has been culled for size" % msg_id)
        _rec = self._records[msg_id]
        self._drop_bytes(_rec)
        _rec.update(rec)
        self._add_bytes(_rec)

    def drop_matching_records(self, check):
        """Remove a record from the DB."""
        matches = self._match(check)
        for rec in matches:
            self._drop_bytes(rec)
            del self._records[rec['msg_id']]

    def drop_record(self, msg_id):
        """Remove a record from the DB."""
        rec = self._records[msg_id]
        self._drop_bytes(rec)
        del self._records[msg_id]

    def find_records(self, check, keys=None):
        """Find records matching a query dict, optionally extracting subset of keys.

        Returns dict keyed by msg_id of matching records.

        Parameters
        ----------

        check: dict
            mongodb-style query argument
        keys: list of strs [optional]
            if specified, the subset of keys to extract.  msg_id will *always* be
            included.
        """
        matches = self._match(check)
        if keys:
            return [ self._extract_subdict(rec, keys) for rec in matches ]
        else:
            return matches

    def get_history(self):
        """get all msg_ids, ordered by time submitted."""
        msg_ids = self._records.keys()
        # Remove any that do not have a submitted timestamp.
        # This is extremely unlikely to happen,
        # but it seems to come up in some tests on VMs.
        msg_ids = [ m for m in msg_ids if self._records[m]['submitted'] is not None ]
        return sorted(msg_ids, key=lambda m: self._records[m]['submitted'])


NODATA = KeyError("NoDB backend doesn't store any data. "
"Start the Controller with a DB backend to enable resubmission / result persistence."
)


class NoDB(BaseDB):
    """A blackhole db backend that actually stores no information.
    
    Provides the full DB interface, but raises KeyErrors on any
    method that tries to access the records.  This can be used to
    minimize the memory footprint of the Hub when its record-keeping
    functionality is not required.
    """
    
    def add_record(self, msg_id, record):
        pass
    
    def get_record(self, msg_id):
        raise NODATA
    
    def update_record(self, msg_id, record):
        pass
    
    def drop_matching_records(self, check):
        pass
    
    def drop_record(self, msg_id):
        pass
    
    def find_records(self, check, keys=None):
        raise NODATA
    
    def get_history(self):
        raise NODATA

