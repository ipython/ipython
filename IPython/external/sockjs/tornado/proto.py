# -*- coding: utf-8 -*-
"""
    sockjs.tornado.proto
    ~~~~~~~~~~~~~~~~~~~~

    SockJS protocol related functions
"""
import logging

# TODO: Add support for ujson module once they can accept unicode strings

# Try to find best json encoder available
try:
    # Check for simplejson
    import simplejson

    json_encode = lambda data: simplejson.dumps(data, separators=(',', ':'))
    json_decode = lambda data: simplejson.loads(data)
    JSONDecodeError = ValueError

    logging.debug('sockjs.tornado will use simplejson module')
except ImportError:
    # Use slow json
    import json

    logging.debug('sockjs.tornado will use json module')

    json_encode = lambda data: json.dumps(data, separators=(',', ':'))
    json_decode = lambda data: json.loads(data)
    JSONDecodeError = ValueError

# Protocol handlers
CONNECT = 'o'
DISCONNECT = 'c'
MESSAGE = 'm'
HEARTBEAT = 'h'


# Various protocol helpers
def disconnect(code, reason):
    """Return SockJS packet with code and close reason

    `code`
        Closing code
    `reason`
        Closing reason
    """
    return 'c[%d,"%s"]' % (code, reason)
