.. _parallel_messages:

Messaging for Parallel Computing
================================

This is an extension of the :ref:`messaging <messaging>` doc. Diagrams of the connections
can be found in the :ref:`parallel connections <parallel_connections>` doc.


ZMQ messaging is also used in the parallel computing IPython system. All messages to/from
kernels remain the same as the single kernel model, and are forwarded through a ZMQ Queue
device. The controller receives all messages and replies in these channels, and saves
results for future use.

The Controller
--------------

The controller is the central collection of processes in the IPython parallel computing
model. It has two major components:

    * The Hub
    * A collection of Schedulers

The Hub
-------

The Hub is the central process for monitoring the state of the engines, and all task
requests and results.  It has no role in execution and does no relay of messages, so
large blocking requests or database actions in the Hub do not have the ability to impede
job submission and results.

Registration (``ROUTER``)
*************************

The first function of the Hub is to facilitate and monitor connections of clients
and engines. Both client and engine registration are handled by the same socket, so only
one ip/port pair is needed to connect any number of connections and clients.

Engines register with the ``zmq.IDENTITY`` of their two ``DEALER`` sockets, one for the
queue, which receives execute requests, and one for the heartbeat, which is used to
monitor the survival of the Engine process.

Message type: ``registration_request``::

    content = {
        'uuid'   : 'abcd-1234-...', # the zmq.IDENTITY of the engine's sockets
    }

.. note::

    these are always the same, at least for now.

The Controller replies to an Engine's registration request with the engine's integer ID,
and all the remaining connection information for connecting the heartbeat process, and
kernel queue socket(s). The message status will be an error if the Engine requests IDs that
already in use.

Message type: ``registration_reply``::

    content = {
        'status' : 'ok', # or 'error'
        # if ok:
        'id' : 0, # int, the engine id
    }

Clients use the same socket as engines to start their connections. Connection requests
from clients need no information:

Message type: ``connection_request``::
    
    content = {}

The reply to a Client registration request contains the connection information for the
multiplexer and load balanced queues, as well as the address for direct hub
queries. If any of these addresses is `None`, that functionality is not available.

Message type: ``connection_reply``::

    content = {
        'status' : 'ok', # or 'error'
    }

Heartbeat
*********

The hub uses a heartbeat system to monitor engines, and track when they become
unresponsive. As described in :ref:`messaging <messaging>`, and shown in :ref:`connections
<parallel_connections>`.

Notification (``PUB``)
**********************

The hub publishes all engine registration/unregistration events on a ``PUB`` socket.
This allows clients to have up-to-date engine ID sets without polling. Registration
notifications contain both the integer engine ID and the queue ID, which is necessary for
sending messages via the Multiplexer Queue and Control Queues.

Message type: ``registration_notification``::

    content = {
        'id' : 0, # engine ID that has been registered
        'uuid' : 'engine_id' # the IDENT for the engine's sockets
    }

Message type : ``unregistration_notification``::

    content = {
        'id' : 0 # engine ID that has been unregistered
        'uuid' : 'engine_id' # the IDENT for the engine's sockets
    }


Client Queries (``ROUTER``)
***************************

The hub monitors and logs all queue traffic, so that clients can retrieve past
results or monitor pending tasks. This information may reside in-memory on the Hub, or
on disk in a database (SQLite and MongoDB are currently supported).  These requests are
handled by the same socket as registration.


:func:`queue_request` requests can specify multiple engines to query via the `targets`
element. A verbose flag can be passed, to determine whether the result should be the list
of `msg_ids` in the queue or simply the length of each list.

Message type: ``queue_request``::

    content = {
        'verbose' : True, # whether return should be lists themselves or just lens
        'targets' : [0,3,1] # list of ints
    }

The content of a reply to a :func:`queue_request` request is a dict, keyed by the engine
IDs. Note that they will be the string representation of the integer keys, since JSON
cannot handle number keys.  The three keys of each dict are::

    'completed' :  messages submitted via any queue that ran on the engine
    'queue' : jobs submitted via MUX queue, whose results have not been received
    'tasks' : tasks that are known to have been submitted to the engine, but 
                have not completed.  Note that with the pure zmq scheduler, this will
                always be 0/[].

Message type: ``queue_reply``::

    content = {
        'status' : 'ok', # or 'error'
        # if verbose=False:
        '0' : {'completed' : 1, 'queue' : 7, 'tasks' : 0},
        # if verbose=True:
        '1' : {'completed' : ['abcd-...','1234-...'], 'queue' : ['58008-'], 'tasks' : []},
    }

Clients can request individual results directly from the hub. This is primarily for
gathering results of executions not submitted by the requesting client, as the client
will have all its own results already. Requests are made by msg_id, and can contain one or
more msg_id. An additional boolean key 'statusonly' can be used to not request the
results, but simply poll the status of the jobs.

Message type: ``result_request``::

    content = {
        'msg_ids' : ['uuid','...'], # list of strs
        'targets' : [1,2,3], # list of int ids or uuids
        'statusonly' : False, # bool
    }

The :func:`result_request` reply contains the content objects of the actual execution
reply messages. If `statusonly=True`, then there will be only the 'pending' and
'completed' lists.  


Message type: ``result_reply``::

    content = {
        'status' : 'ok', # else error
        # if ok:
        'acbd-...' : msg, # the content dict is keyed by msg_ids,
                         # values are the result messages
                        # there will be none of these if `statusonly=True`
        'pending' : ['msg_id','...'], # msg_ids still pending
        'completed' : ['msg_id','...'], # list of completed msg_ids
    }
    buffers = ['bufs','...'] # the buffers that contained the results of the objects.
                            # this will be empty if no messages are complete, or if 
                            # statusonly is True.

For memory management purposes, Clients can also instruct the hub to forget the
results of messages. This can be done by message ID or engine ID. Individual messages are
dropped by msg_id, and all messages completed on an engine are dropped by engine ID. This
may no longer be necessary with the mongodb-based message logging backend.

If the msg_ids element is the string ``'all'`` instead of a list, then all completed
results are forgotten.

Message type: ``purge_request``::

    content = {
        'msg_ids' : ['id1', 'id2',...], # list of msg_ids or 'all'
        'engine_ids' : [0,2,4] # list of engine IDs
    }

The reply to a purge request is simply the status 'ok' if the request succeeded, or an
explanation of why it failed, such as requesting the purge of a nonexistent or pending
message.

Message type: ``purge_reply``::

    content = {
        'status' : 'ok', # or 'error'
    }


Schedulers
----------

There are three basic schedulers:

  * Task Scheduler
  * MUX Scheduler
  * Control Scheduler

The MUX and Control schedulers are simple MonitoredQueue ØMQ devices, with ``ROUTER``
sockets on either side. This allows the queue to relay individual messages to particular
targets via ``zmq.IDENTITY`` routing. The Task scheduler may be a MonitoredQueue ØMQ
device, in which case the client-facing socket is ``ROUTER``, and the engine-facing socket
is ``DEALER``.  The result of this is that client-submitted messages are load-balanced via 
the ``DEALER`` socket, but the engine's replies to each message go to the requesting client.

Raw ``DEALER`` scheduling is quite primitive, and doesn't allow message introspection, so
there are also Python Schedulers that can be used. These Schedulers behave in much the
same way as a MonitoredQueue does from the outside, but have rich internal logic to
determine destinations, as well as handle dependency graphs Their sockets are always
``ROUTER`` on both sides.

The Python task schedulers have an additional message type, which informs the Hub of
the destination of a task as soon as that destination is known.

Message type: ``task_destination``::

    content = {
        'msg_id' : 'abcd-1234-...', # the msg's uuid
        'engine_id' : '1234-abcd-...', # the destination engine's zmq.IDENTITY
    }

:func:`apply`
*************

In terms of message classes, the MUX scheduler and Task scheduler relay the exact same
message types.  Their only difference lies in how the destination is selected.

The `Namespace <http://gist.github.com/483294>`_ model suggests that execution be able to
use the model::

    ns.apply(f, *args, **kwargs)
    
which takes `f`, a function in the user's namespace, and executes ``f(*args, **kwargs)``
on a remote engine, returning the result (or, for non-blocking, information facilitating
later retrieval of the result). This model, unlike the execute message which just uses a
code string, must be able to send arbitrary (pickleable) Python objects. And ideally, copy
as little data as we can. The `buffers` property of a Message was introduced for this
purpose.

Utility method :func:`build_apply_message` in :mod:`IPython.kernel.zmq.serialize` wraps a
function signature and builds a sendable buffer format for minimal data copying (exactly
zero copies of numpy array data or buffers or large strings).

Message type: ``apply_request``::

    metadata = {
        'after' : ['msg_id',...], # list of msg_ids or output of Dependency.as_dict()
        'follow' : ['msg_id',...], # list of msg_ids or output of Dependency.as_dict()
    }
    content = {}
    buffers = ['...'] # at least 3 in length
                    # as built by build_apply_message(f,args,kwargs)

after/follow represent task dependencies. 'after' corresponds to a time dependency. The
request will not arrive at an engine until the 'after' dependency tasks have completed.
'follow' corresponds to a location dependency. The task will be submitted to the same
engine as these msg_ids (see :class:`Dependency` docs for details).

Message type: ``apply_reply``::

    content = {
        'status' : 'ok' # 'ok' or 'error'
        # other error info here, as in other messages
    }
    buffers = ['...'] # either 1 or 2 in length
                    # a serialization of the return value of f(*args,**kwargs)
                    # only populated if status is 'ok'

All engine execution and data movement is performed via apply messages.

Control Messages
----------------

Messages that interact with the engines, but are not meant to execute code, are submitted
via the Control queue. These messages have high priority, and are thus received and
handled before any execution requests.

Clients may want to clear the namespace on the engine. There are no arguments nor
information involved in this request, so the content is empty.

Message type: ``clear_request``::

    content = {}

Message type: ``clear_reply``::

    content = {
        'status' : 'ok' # 'ok' or 'error'
        # other error info here, as in other messages
    }

Clients may want to abort tasks that have not yet run. This can by done by message id, or
all enqueued messages can be aborted if None is specified.

Message type: ``abort_request``::

    content = {
        'msg_ids' : ['1234-...', '...'] # list of msg_ids or None
    }

Message type: ``abort_reply``::

    content = {
        'status' : 'ok' # 'ok' or 'error'
        # other error info here, as in other messages
    }

The last action a client may want to do is shutdown the kernel. If a kernel receives a
shutdown request, then it aborts all queued messages, replies to the request, and exits.

Message type: ``shutdown_request``::

    content = {}

Message type: ``shutdown_reply``::

    content = {
        'status' : 'ok' # 'ok' or 'error'
        # other error info here, as in other messages
    }


Implementation
--------------

There are a few differences in implementation between the `StreamSession` object used in
the newparallel branch and the `Session` object, the main one being that messages are
sent in parts, rather than as a single serialized object. `StreamSession` objects also
take pack/unpack functions, which are to be used when serializing/deserializing objects.
These can be any functions that translate to/from formats that ZMQ sockets can send
(buffers,bytes, etc.).

Split Sends
***********

Previously, messages were bundled as a single json object and one call to
:func:`socket.send_json`. Since the hub inspects all messages, and doesn't need to
see the content of the messages, which can be large, messages are now serialized and sent in
pieces. All messages are sent in at least 4 parts: the header, the parent header, the metadata and the content.
This allows the controller to unpack and inspect the (always small) header,
without spending time unpacking the content unless the message is bound for the
controller. Buffers are added on to the end of the message, and can be any objects that
present the buffer interface.

