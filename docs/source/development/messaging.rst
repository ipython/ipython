=====================
Message Specification
=====================

Note: not all of these have yet been fully fleshed out, but the key ones are,
see kernel and frontend files for actual implementation details.

General Message Format
=====================

General message format::

    {
        header : { 'msg_id' : 10,    # start with 0
	           'username' : 'name',
		   'session' : uuid
		   },
	parent_header : dict,
        msg_type : 'string_message_type',
        content : blackbox_dict , # Must be a dict
    }

Side effect: (PUB/SUB)
======================

# msg_type = 'stream'
content = {
    name : 'stdout',
    data : 'blob',
}

# msg_type = 'pyin'
content = {
    code = 'x=1',
}

# msg_type = 'pyout'
content = {
    data = 'repr(obj)',
    prompt_number = 10
}

# msg_type = 'pyerr'
content = {
    traceback : 'full traceback',
    exc_type : 'TypeError',
    exc_value :  'msg'
}

# msg_type = 'file'
content = {
    path = 'cool.jpg',
    data : 'blob'
}

Request/Reply
=============

Execute
-------

Request:

# msg_type = 'execute_request'
content = {
    code : 'a = 10',
}

Reply:

# msg_type = 'execute_reply'
content = {
  'status' : 'ok' OR 'error' OR 'abort'
  # data depends on status value
}

Complete
--------

# msg_type = 'complete_request'
content = {
    text : 'a.f',    # complete on this
    line : 'print a.f'    # full line
}

# msg_type = 'complete_reply'
content = {
    matches : ['a.foo', 'a.bar']
}

Control
-------

# msg_type = 'heartbeat'
content = {

}
