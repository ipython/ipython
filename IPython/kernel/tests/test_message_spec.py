"""Test suite for our zeromq-based message specification."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import re
import sys
from distutils.version import LooseVersion as V
try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

import nose.tools as nt

from IPython.utils.traitlets import (
    HasTraits, TraitError, Bool, Unicode, Dict, Integer, List, Enum,
)
from IPython.utils.py3compat import string_types, iteritems
from IPython.testing.messagespec import *

from .utils import TIMEOUT, start_global_kernel, flush_channels, execute

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
KC = None

def setup():
    global KC
    KC = start_global_kernel()


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

# Shell channel

def test_execute():
    flush_channels()
    
    msg_id = KC.execute(code='x=1')
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'execute_reply', msg_id)


def test_execute_silent():
    flush_channels()
    msg_id, reply = execute(code='x=1', silent=True)
    
    # flush status=idle
    status = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(status, 'status', msg_id)
    nt.assert_equal(status['content']['execution_state'], 'idle')

    nt.assert_raises(Empty, KC.iopub_channel.get_msg, timeout=0.1)
    count = reply['execution_count']
    
    msg_id, reply = execute(code='x=2', silent=True)
    
    # flush status=idle
    status = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(status, 'status', msg_id)
    nt.assert_equal(status['content']['execution_state'], 'idle')
    
    nt.assert_raises(Empty, KC.iopub_channel.get_msg, timeout=0.1)
    count_2 = reply['execution_count']
    nt.assert_equal(count_2, count)


def test_execute_error():
    flush_channels()
    
    msg_id, reply = execute(code='1/0')
    nt.assert_equal(reply['status'], 'error')
    nt.assert_equal(reply['ename'], 'ZeroDivisionError')
    
    error = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(error, 'error', msg_id)


def test_execute_inc():
    """execute request should increment execution_count"""
    flush_channels()

    msg_id, reply = execute(code='x=1')
    count = reply['execution_count']
    
    flush_channels()
    
    msg_id, reply = execute(code='x=2')
    count_2 = reply['execution_count']
    nt.assert_equal(count_2, count+1)


def test_user_expressions():
    flush_channels()

    msg_id, reply = execute(code='x=1', user_expressions=dict(foo='x+1'))
    user_expressions = reply['user_expressions']
    nt.assert_equal(user_expressions, {u'foo': {
        u'status': u'ok',
        u'data': {u'text/plain': u'2'},
        u'metadata': {},
    }})


def test_user_expressions_fail():
    flush_channels()

    msg_id, reply = execute(code='x=0', user_expressions=dict(foo='nosuchname'))
    user_expressions = reply['user_expressions']
    foo = user_expressions['foo']
    nt.assert_equal(foo['status'], 'error')
    nt.assert_equal(foo['ename'], 'NameError')


def test_oinfo():
    flush_channels()

    msg_id = KC.inspect('a')
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)


def test_oinfo_found():
    flush_channels()

    msg_id, reply = execute(code='a=5')
    
    msg_id = KC.inspect('a')
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)
    content = reply['content']
    assert content['found']
    text = content['data']['text/plain']
    nt.assert_in('Type:', text)
    nt.assert_in('Docstring:', text)


def test_oinfo_detail():
    flush_channels()

    msg_id, reply = execute(code='ip=get_ipython()')
    
    msg_id = KC.inspect('ip.object_inspect', cursor_pos=10, detail_level=1)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)
    content = reply['content']
    assert content['found']
    text = content['data']['text/plain']
    nt.assert_in('Definition:', text)
    nt.assert_in('Source:', text)


def test_oinfo_not_found():
    flush_channels()

    msg_id = KC.inspect('dne')
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)
    content = reply['content']
    nt.assert_false(content['found'])


def test_complete():
    flush_channels()

    msg_id, reply = execute(code="alpha = albert = 5")
    
    msg_id = KC.complete('al', 2)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'complete_reply', msg_id)
    matches = reply['content']['matches']
    for name in ('alpha', 'albert'):
        nt.assert_in(name, matches)


def test_kernel_info_request():
    flush_channels()

    msg_id = KC.kernel_info()
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'kernel_info_reply', msg_id)


def test_single_payload():
    flush_channels()
    msg_id, reply = execute(code="for i in range(3):\n"+
                                 "   x=range?\n")
    payload = reply['payload']
    next_input_pls = [pl for pl in payload if pl["source"] == "set_next_input"]
    nt.assert_equal(len(next_input_pls), 1)

def test_is_complete():
    flush_channels()

    msg_id = KC.is_complete("a = 1")
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'is_complete_reply', msg_id)

def test_history_range():
    flush_channels()
    
    msg_id_exec = KC.execute(code='x=1', store_history = True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)
    
    msg_id = KC.history(hist_access_type = 'range', raw = True, output = True, start = 1, stop = 2, session = 0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    nt.assert_equal(len(content['history']), 1)

def test_history_tail():
    flush_channels()
    
    msg_id_exec = KC.execute(code='x=1', store_history = True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)
    
    msg_id = KC.history(hist_access_type = 'tail', raw = True, output = True, n = 1, session = 0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    nt.assert_equal(len(content['history']), 1)

def test_history_search():
    flush_channels()
    
    msg_id_exec = KC.execute(code='x=1', store_history = True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)
    
    msg_id = KC.history(hist_access_type = 'search', raw = True, output = True, n = 1, pattern = '*', session = 0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    nt.assert_equal(len(content['history']), 1)

# IOPub channel


def test_stream():
    flush_channels()

    msg_id, reply = execute("print('hi')")

    stdout = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(stdout, 'stream', msg_id)
    content = stdout['content']
    nt.assert_equal(content['text'], u'hi\n')


def test_display_data():
    flush_channels()

    msg_id, reply = execute("from IPython.core.display import display; display(1)")
    
    display = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(display, 'display_data', parent=msg_id)
    data = display['content']['data']
    nt.assert_equal(data['text/plain'], u'1')

