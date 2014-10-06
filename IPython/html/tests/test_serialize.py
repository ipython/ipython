"""Test serialize/deserialize messages with buffers"""

import os

import nose.tools as nt

from IPython.kernel.zmq.session import Session
from ..base.zmqhandlers import (
    serialize_binary_message,
    deserialize_binary_message,
)

def test_serialize_binary():
    s = Session()
    msg = s.msg('data_pub', content={'a': 'b'})
    msg['buffers'] = [ os.urandom(3) for i in range(3) ]
    bmsg = serialize_binary_message(msg)
    nt.assert_is_instance(bmsg, bytes)

def test_deserialize_binary():
    s = Session()
    msg = s.msg('data_pub', content={'a': 'b'})
    msg['buffers'] = [ os.urandom(2) for i in range(3) ]
    bmsg = serialize_binary_message(msg)
    msg2 = deserialize_binary_message(bmsg)
    nt.assert_equal(msg2, msg)
