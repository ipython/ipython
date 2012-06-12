.. _parallel_db:

=======================
IPython's Task Database
=======================

Enabling a DB Backend
=====================

The IPython Hub can store all task requests and results in a database. 
Currently supported backends are: MongoDB, SQLite, and an in-memory DictDB.

This database behavior is optional due to its potential :ref:`db_cost`,
so you must enable one, either at the command-line::

    $> ipcontroller --dictb # or --mongodb or --sqlitedb

or in your :file:`ipcontroller_config.py`:

.. sourcecode:: python

    c.HubFactory.db_class = "DictDB"
    c.HubFactory.db_class = "MongoDB"
    c.HubFactory.db_class = "SQLiteDB"


Using the Task Database
=======================

The most common use case for this is clients requesting results for tasks they did not submit, via:

.. sourcecode:: ipython

    In [1]: rc.get_result(task_id)

However, since we have this DB backend, we provide a direct query method in the :class:`~.Client`
for users who want deeper introspection into their task history. The :meth:`db_query` method of
the Client is modeled after MongoDB queries, so if you have used MongoDB it should look
familiar.  In fact, when the MongoDB backend is in use, the query is relayed directly.  
When using other backends, the interface is emulated and only a subset of queries is possible.

.. seealso::

    MongoDB query docs: http://www.mongodb.org/display/DOCS/Querying

:meth:`Client.db_query` takes a dictionary query object, with keys from the TaskRecord key list,
and values of either exact values to test, or MongoDB queries, which are dicts of The form:
``{'operator' : 'argument(s)'}``. There is also an optional `keys` argument, that specifies
which subset of keys should be retrieved. The default is to retrieve all keys excluding the
request and result buffers. :meth:`db_query` returns a list of TaskRecord dicts. Also like
MongoDB, the `msg_id` key will always be included, whether requested or not.

TaskRecord keys:

=============== =============== =============
Key             Type            Description
=============== =============== =============
msg_id          uuid(ascii)     The msg ID
header          dict            The request header
content         dict            The request content (likely empty)
buffers         list(bytes)     buffers containing serialized request objects
submitted       datetime        timestamp for time of submission (set by client)
client_uuid     uuid(ascii)     IDENT of client's socket
engine_uuid     uuid(ascii)     IDENT of engine's socket
started         datetime        time task began execution on engine
completed       datetime        time task finished execution (success or failure) on engine
resubmitted     uuid(ascii)     msg_id of resubmitted task (if applicable)
result_header   dict            header for result
result_content  dict            content for result
result_buffers  list(bytes)     buffers containing serialized request objects
queue           str             The name of the queue for the task ('mux' or 'task')
pyin            str             Python input source
pyout           dict            Python output (pyout message content)
pyerr           dict            Python traceback (pyerr message content)
stdout          str             Stream of stdout data
stderr          str             Stream of stderr data

=============== =============== =============

MongoDB operators we emulate on all backends:

==========  =================
Operator    Python equivalent
==========  =================
  '$in'       in
  '$nin'      not in
  '$eq'       ==
  '$ne'       !=
  '$ge'       >
  '$gte'      >=
  '$le'       <
  '$lte'      <=
==========  =================


The DB Query is useful for two primary cases:

1. deep polling of task status or metadata
2. selecting a subset of tasks, on which to perform a later operation (e.g. wait on result, purge records, resubmit,...)


Example Queries
===============

To get all msg_ids that are not completed, only retrieving their ID and start time:

.. sourcecode:: ipython

    In [1]: incomplete = rc.db_query({'completed' : None}, keys=['msg_id', 'started'])

All jobs started in the last hour by me:

.. sourcecode:: ipython

    In [1]: from datetime import datetime, timedelta

    In [2]: hourago = datetime.now() - timedelta(1./24)

    In [3]: recent = rc.db_query({'started' : {'$gte' : hourago },
                                    'client_uuid' : rc.session.session})

All jobs started more than an hour ago, by clients *other than me*:

.. sourcecode:: ipython

    In [3]: recent = rc.db_query({'started' : {'$le' : hourago },
                                    'client_uuid' : {'$ne' : rc.session.session}})

Result headers for all jobs on engine 3 or 4:

.. sourcecode:: ipython

    In [1]: uuids = map(rc._engines.get, (3,4))

    In [2]: hist34 = rc.db_query({'engine_uuid' : {'$in' : uuids }, keys='result_header')

.. _db_cost:

Cost
====

The advantage of the database backends is, of course, that large amounts of
data can be stored that won't fit in memory.  The basic DictDB 'backend' is actually
to just store all of this information in a Python dictionary.  This is very fast,
but will run out of memory quickly if you move a lot of data around, or your
cluster is to run for a long time.

Unfortunately, the DB backends (SQLite and MongoDB) right now are rather slow,
and can still consume large amounts of resources, particularly if large tasks
or results are being created at a high frequency.

For this reason, we have added :class:`~.NoDB`,a dummy backend that doesn't
actually store any information. When you use this database, nothing is stored,
and any request for results will result in a KeyError.  This obviously prevents
later requests for results and task resubmission from functioning, but
sometimes those nice features are not as useful as keeping Hub memory under
control.


