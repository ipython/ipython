"""A TaskRecord backend using sqlite3

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import json
import os
import cPickle as pickle
from datetime import datetime

try:
    import sqlite3
except ImportError:
    sqlite3 = None

from zmq.eventloop import ioloop

from IPython.utils.traitlets import Unicode, Instance, List, Dict
from .dictdb import BaseDB
from IPython.utils.jsonutil import date_default, extract_dates, squash_dates

#-----------------------------------------------------------------------------
# SQLite operators, adapters, and converters
#-----------------------------------------------------------------------------

try:
    buffer
except NameError:
    # py3k
    buffer = memoryview

operators = {
 '$lt' : "<",
 '$gt' : ">",
 # null is handled weird with ==,!=
 '$eq' : "=",
 '$ne' : "!=",
 '$lte': "<=",
 '$gte': ">=",
 '$in' : ('=', ' OR '),
 '$nin': ('!=', ' AND '),
 # '$all': None,
 # '$mod': None,
 # '$exists' : None
}
null_operators = {
'=' : "IS NULL",
'!=' : "IS NOT NULL",
}

def _adapt_dict(d):
    return json.dumps(d, default=date_default)

def _convert_dict(ds):
    if ds is None:
        return ds
    else:
        if isinstance(ds, bytes):
            # If I understand the sqlite doc correctly, this will always be utf8
            ds = ds.decode('utf8')
        return extract_dates(json.loads(ds))

def _adapt_bufs(bufs):
    # this is *horrible*
    # copy buffers into single list and pickle it:
    if bufs and isinstance(bufs[0], (bytes, buffer)):
        return sqlite3.Binary(pickle.dumps(map(bytes, bufs),-1))
    elif bufs:
        return bufs
    else:
        return None

def _convert_bufs(bs):
    if bs is None:
        return []
    else:
        return pickle.loads(bytes(bs))

#-----------------------------------------------------------------------------
# SQLiteDB class
#-----------------------------------------------------------------------------

class SQLiteDB(BaseDB):
    """SQLite3 TaskRecord backend."""

    filename = Unicode('tasks.db', config=True,
        help="""The filename of the sqlite task database. [default: 'tasks.db']""")
    location = Unicode('', config=True,
        help="""The directory containing the sqlite task database.  The default
        is to use the cluster_dir location.""")
    table = Unicode("", config=True,
        help="""The SQLite Table to use for storing tasks for this session. If unspecified,
        a new table will be created with the Hub's IDENT.  Specifying the table will result
        in tasks from previous sessions being available via Clients' db_query and
        get_result methods.""")

    if sqlite3 is not None:
        _db = Instance('sqlite3.Connection')
    else:
        _db = None
    # the ordered list of column names
    _keys = List(['msg_id' ,
            'header' ,
            'metadata',
            'content',
            'buffers',
            'submitted',
            'client_uuid' ,
            'engine_uuid' ,
            'started',
            'completed',
            'resubmitted',
            'received',
            'result_header' ,
            'result_metadata',
            'result_content' ,
            'result_buffers' ,
            'queue' ,
            'pyin' ,
            'pyout',
            'pyerr',
            'stdout',
            'stderr',
        ])
    # sqlite datatypes for checking that db is current format
    _types = Dict({'msg_id' : 'text' ,
            'header' : 'dict text',
            'metadata' : 'dict text',
            'content' : 'dict text',
            'buffers' : 'bufs blob',
            'submitted' : 'timestamp',
            'client_uuid' : 'text',
            'engine_uuid' : 'text',
            'started' : 'timestamp',
            'completed' : 'timestamp',
            'resubmitted' : 'text',
            'received' : 'timestamp',
            'result_header' : 'dict text',
            'result_metadata' : 'dict text',
            'result_content' : 'dict text',
            'result_buffers' : 'bufs blob',
            'queue' : 'text',
            'pyin' : 'text',
            'pyout' : 'text',
            'pyerr' : 'text',
            'stdout' : 'text',
            'stderr' : 'text',
        })

    def __init__(self, **kwargs):
        super(SQLiteDB, self).__init__(**kwargs)
        if sqlite3 is None:
            raise ImportError("SQLiteDB requires sqlite3")
        if not self.table:
            # use session, and prefix _, since starting with # is illegal
            self.table = '_'+self.session.replace('-','_')
        if not self.location:
            # get current profile
            from IPython.core.application import BaseIPythonApplication
            if BaseIPythonApplication.initialized():
                app = BaseIPythonApplication.instance()
                if app.profile_dir is not None:
                    self.location = app.profile_dir.location
                else:
                    self.location = u'.'
            else:
                self.location = u'.'
        self._init_db()

        # register db commit as 2s periodic callback
        # to prevent clogging pipes
        # assumes we are being run in a zmq ioloop app
        loop = ioloop.IOLoop.instance()
        pc = ioloop.PeriodicCallback(self._db.commit, 2000, loop)
        pc.start()

    def _defaults(self, keys=None):
        """create an empty record"""
        d = {}
        keys = self._keys if keys is None else keys
        for key in keys:
            d[key] = None
        return d

    def _check_table(self):
        """Ensure that an incorrect table doesn't exist

        If a bad (old) table does exist, return False
        """
        cursor = self._db.execute("PRAGMA table_info(%s)"%self.table)
        lines = cursor.fetchall()
        if not lines:
            # table does not exist
            return True
        types = {}
        keys = []
        for line in lines:
            keys.append(line[1])
            types[line[1]] = line[2]
        if self._keys != keys:
            # key mismatch
            self.log.warn('keys mismatch')
            return False
        for key in self._keys:
            if types[key] != self._types[key]:
                self.log.warn(
                    'type mismatch: %s: %s != %s'%(key,types[key],self._types[key])
                )
                return False
        return True

    def _init_db(self):
        """Connect to the database and get new session number."""
        # register adapters
        sqlite3.register_adapter(dict, _adapt_dict)
        sqlite3.register_converter('dict', _convert_dict)
        sqlite3.register_adapter(list, _adapt_bufs)
        sqlite3.register_converter('bufs', _convert_bufs)
        # connect to the db
        dbfile = os.path.join(self.location, self.filename)
        self._db = sqlite3.connect(dbfile, detect_types=sqlite3.PARSE_DECLTYPES,
            # isolation_level = None)#,
             cached_statements=64)
        # print dir(self._db)
        first_table = previous_table = self.table
        i=0
        while not self._check_table():
            i+=1
            self.table = first_table+'_%i'%i
            self.log.warn(
                "Table %s exists and doesn't match db format, trying %s"%
                (previous_table, self.table)
            )
            previous_table = self.table

        self._db.execute("""CREATE TABLE IF NOT EXISTS %s
                (msg_id text PRIMARY KEY,
                header dict text,
                metadata dict text,
                content dict text,
                buffers bufs blob,
                submitted timestamp,
                client_uuid text,
                engine_uuid text,
                started timestamp,
                completed timestamp,
                resubmitted text,
                received timestamp,
                result_header dict text,
                result_metadata dict text,
                result_content dict text,
                result_buffers bufs blob,
                queue text,
                pyin text,
                pyout text,
                pyerr text,
                stdout text,
                stderr text)
                """%self.table)
        self._db.commit()

    def _dict_to_list(self, d):
        """turn a mongodb-style record dict into a list."""

        return [ d[key] for key in self._keys ]

    def _list_to_dict(self, line, keys=None):
        """Inverse of dict_to_list"""
        keys = self._keys if keys is None else keys
        d = self._defaults(keys)
        for key,value in zip(keys, line):
            d[key] = value

        return d

    def _render_expression(self, check):
        """Turn a mongodb-style search dict into an SQL query."""
        expressions = []
        args = []

        skeys = set(check.keys())
        skeys.difference_update(set(self._keys))
        skeys.difference_update(set(['buffers', 'result_buffers']))
        if skeys:
            raise KeyError("Illegal testing key(s): %s"%skeys)

        for name,sub_check in check.iteritems():
            if isinstance(sub_check, dict):
                for test,value in sub_check.iteritems():
                    try:
                        op = operators[test]
                    except KeyError:
                        raise KeyError("Unsupported operator: %r"%test)
                    if isinstance(op, tuple):
                        op, join = op

                    if value is None and op in null_operators:
                        expr = "%s %s" % (name, null_operators[op])
                    else:
                        expr = "%s %s ?"%(name, op)
                        if isinstance(value, (tuple,list)):
                            if op in null_operators and any([v is None for v in value]):
                                # equality tests don't work with NULL
                                raise ValueError("Cannot use %r test with NULL values on SQLite backend"%test)
                            expr = '( %s )'%( join.join([expr]*len(value)) )
                            args.extend(value)
                        else:
                            args.append(value)
                    expressions.append(expr)
            else:
                # it's an equality check
                if sub_check is None:
                    expressions.append("%s IS NULL" % name)
                else:
                    expressions.append("%s = ?"%name)
                    args.append(sub_check)

        expr = " AND ".join(expressions)
        return expr, args

    def add_record(self, msg_id, rec):
        """Add a new Task Record, by msg_id."""
        d = self._defaults()
        d.update(rec)
        d['msg_id'] = msg_id
        line = self._dict_to_list(d)
        tups = '(%s)'%(','.join(['?']*len(line)))
        self._db.execute("INSERT INTO %s VALUES %s"%(self.table, tups), line)
        # self._db.commit()

    def get_record(self, msg_id):
        """Get a specific Task Record, by msg_id."""
        cursor = self._db.execute("""SELECT * FROM %s WHERE msg_id==?"""%self.table, (msg_id,))
        line = cursor.fetchone()
        if line is None:
            raise KeyError("No such msg: %r"%msg_id)
        return self._list_to_dict(line)

    def update_record(self, msg_id, rec):
        """Update the data in an existing record."""
        query = "UPDATE %s SET "%self.table
        sets = []
        keys = sorted(rec.keys())
        values = []
        for key in keys:
            sets.append('%s = ?'%key)
            values.append(rec[key])
        query += ', '.join(sets)
        query += ' WHERE msg_id == ?'
        values.append(msg_id)
        self._db.execute(query, values)
        # self._db.commit()

    def drop_record(self, msg_id):
        """Remove a record from the DB."""
        self._db.execute("""DELETE FROM %s WHERE msg_id==?"""%self.table, (msg_id,))
        # self._db.commit()

    def drop_matching_records(self, check):
        """Remove a record from the DB."""
        expr,args = self._render_expression(check)
        query = "DELETE FROM %s WHERE %s"%(self.table, expr)
        self._db.execute(query,args)
        # self._db.commit()

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
        if keys:
            bad_keys = [ key for key in keys if key not in self._keys ]
            if bad_keys:
                raise KeyError("Bad record key(s): %s"%bad_keys)

        if keys:
            # ensure msg_id is present and first:
            if 'msg_id' in keys:
                keys.remove('msg_id')
            keys.insert(0, 'msg_id')
            req = ', '.join(keys)
        else:
            req = '*'
        expr,args = self._render_expression(check)
        query = """SELECT %s FROM %s WHERE %s"""%(req, self.table, expr)
        cursor = self._db.execute(query, args)
        matches = cursor.fetchall()
        records = []
        for line in matches:
            rec = self._list_to_dict(line, keys)
            records.append(rec)
        return records

    def get_history(self):
        """get all msg_ids, ordered by time submitted."""
        query = """SELECT msg_id FROM %s ORDER by submitted ASC"""%self.table
        cursor = self._db.execute(query)
        # will be a list of length 1 tuples
        return [ tup[0] for tup in cursor.fetchall()]

__all__ = ['SQLiteDB']