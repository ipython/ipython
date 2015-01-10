"""A simple tool to test the ZMQ kernel by publishing messages and checking the response."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import

import atexit

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

import nose.tools as nt

from IPython.kernel import manager

from IPython.testing.messagespec import *

#-------------------------------------------------------------------------------
# Globals
#-------------------------------------------------------------------------------

STARTUP_TIMEOUT = 60
TIMEOUT = 15

KM = None
KC = None

#-------------------------------------------------------------------------------
# Code to setup the kernel for testing
#-------------------------------------------------------------------------------

def start_new_kernel(kernel = 'python',**kwargs):
    """start a new kernel, and return its Manager and Client
    """
    return manager.start_new_kernel(startup_timeout=STARTUP_TIMEOUT, kernel_name = kernel, **kwargs)

def flush_channels(kc=None):
    """flush any messages waiting on the queue"""

    if kc is None:
        kc = KC
    for channel in (kc.shell_channel, kc.iopub_channel):
        while True:
            try:
                msg = channel.get_msg(block=True, timeout=0.1)
            except Empty:
                break
            else:
                validate_message(msg)

def execute(code='', kc=None, **kwargs):
    """wrapper for doing common steps for validating an execution request"""
    if kc is None:
        kc = KC
    msg_id = kc.execute(code=code, **kwargs)
    reply = kc.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'execute_reply', msg_id)
    busy = kc.get_iopub_msg(timeout=TIMEOUT)
    validate_message(busy, 'status', msg_id)
    nt.assert_equal(busy['content']['execution_state'], 'busy')
    
    if not kwargs.get('silent'):
        execute_input = kc.get_iopub_msg(timeout=TIMEOUT)
        validate_message(execute_input, 'execute_input', msg_id)
        nt.assert_equal(execute_input['content']['code'], code)
    
    return msg_id, reply['content']

def start_global_kernel(kernel='python'):
    """start the global kernel (if it isn't running) and return its client"""
    global KM, KC
    if KM is None:
        KM, KC = start_new_kernel(kernel)
        atexit.register(stop_global_kernel)
    else:
        flush_channels(KC)
    return KC

def stop_global_kernel():
    """Stop the global shared kernel instance, if it exists"""
    global KM, KC
    KC.stop_channels()
    KC = None
    if KM is None:
        return
    KM.shutdown_kernel(now=True)
    KM = None

#-----------------------------------------------------------------------------
# Test methods
#-----------------------------------------------------------------------------

# Shell channel

def test_execute(test_code):
    flush_channels()
    
    msg_id = KC.execute(code=test_code)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'execute_reply', msg_id)


def test_execute_silent(test_code):
    flush_channels()
    msg_id, reply = execute(code=test_code, silent=True)
    
    # flush status=idle
    status = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(status, 'status', msg_id)
    nt.assert_equal(status['content']['execution_state'], 'idle')

    nt.assert_raises(Empty, KC.iopub_channel.get_msg, timeout=0.1)
    count = reply['execution_count']
    
    msg_id, reply = execute(code=test_code, silent=True)
    
    # flush status=idle
    status = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(status, 'status', msg_id)
    nt.assert_equal(status['content']['execution_state'], 'idle')
    
    nt.assert_raises(Empty, KC.iopub_channel.get_msg, timeout=0.1)
    count_2 = reply['execution_count']
    nt.assert_equal(count_2, count)


def test_execute_error(test_code, error_name = None):
    flush_channels()
    
    msg_id, reply = execute(code=test_code)
    nt.assert_equal(reply['status'], 'error')
    if error_name:
        nt.assert_equal(reply['ename'], error_name)
    
    error = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(error, 'error', msg_id)


def test_execute_inc(test_code):
    """execute request should increment execution_count"""
    flush_channels()

    msg_id, reply = execute(code=test_code)
    count = reply['execution_count']
    
    flush_channels()
    
    msg_id, reply = execute(code=test_code)
    count_2 = reply['execution_count']
    nt.assert_equal(count_2, count+1)


def test_user_expressions(test_code,user_expression,user_expression_result):
    flush_channels()

    msg_id, reply = execute(code=test_code, user_expressions=dict(foo=user_expression))
    user_expressions = reply['user_expressions']
    nt.assert_equal(user_expressions, {u'foo': {
        u'status': u'ok',
        u'data': {u'text/plain': user_expression_result},
        u'metadata': {},
    }})


def test_user_expressions_fail(test_code, user_expression, user_expression_error = None):
    flush_channels()

    msg_id, reply = execute(code=test_code, user_expressions=dict(foo=user_expression))
    user_expressions = reply['user_expressions']
    foo = user_expressions['foo']
    nt.assert_equal(foo['status'], 'error')
    if user_expression_error:
        nt.assert_equal(foo['ename'], user_expression_error)


def test_oinfo(inspect_object):
    flush_channels()

    msg_id = KC.inspect(inspect_object)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)


def test_oinfo_found(test_code,inspect_object):
    flush_channels()

    msg_id, reply = execute(code=test_code)
    
    msg_id = KC.inspect(inpect_object)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)
    content = reply['content']
    assert content['found']
    text = content['data']['text/plain']
    nt.assert_in('Type:', text)
    nt.assert_in('Docstring:', text)


def test_oinfo_detail(test_code, inspect_object, inspect_position):
    flush_channels()

    msg_id, reply = execute(code=test_code)
    
    msg_id = KC.inspect(inspect_object, cursor_pos=inspect_position, detail_level=1)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)
    content = reply['content']
    assert content['found']
    text = content['data']['text/plain']
    nt.assert_in('Definition:', text)
    nt.assert_in('Source:', text)


def test_oinfo_not_found(inspect_object):
    flush_channels()

    msg_id = KC.inspect(inspect_object)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)
    content = reply['content']
    nt.assert_false(content['found'])


def test_complete(test_code, complete_string, complete_results):
    flush_channels()

    msg_id, reply = execute(code=test_code)
    
    msg_id = KC.complete(complete_string, 2)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'complete_reply', msg_id)
    matches = reply['content']['matches']
    for name in complete_results:
        nt.assert_in(name, matches)


def test_kernel_info_request():
    flush_channels()

    msg_id = KC.kernel_info()
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'kernel_info_reply', msg_id)


def test_single_payload(test_code):
    flush_channels()
    msg_id, reply = execute(code=test_code)
    payload = reply['payload']
    next_input_pls = [pl for pl in payload if pl["source"] == "set_next_input"]
    nt.assert_equal(len(next_input_pls), 1)

def test_is_complete(test_code):
    flush_channels()

    msg_id = KC.is_complete(test_code)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'is_complete_reply', msg_id)

def test_history_range(test_code):
    flush_channels()
    
    msg_id_exec = KC.execute(code=test_code, store_history = True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)
    
    msg_id = KC.history(hist_access_type = 'range', raw = True, output = True, start = 1, stop = 2, session = 0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    nt.assert_equal(len(content['history']), 1)

def test_history_tail(test_code):
    flush_channels()
    
    msg_id_exec = KC.execute(code=test_code, store_history = True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)
    
    msg_id = KC.history(hist_access_type = 'tail', raw = True, output = True, n = 1, session = 0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    nt.assert_equal(len(content['history']), 1)

def test_history_search(test_code):
    flush_channels()
    
    msg_id_exec = KC.execute(code=test_code, store_history = True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)
    
    msg_id = KC.history(hist_access_type = 'search', raw = True, output = True, n = 1, pattern = '*', session = 0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    nt.assert_equal(len(content['history']), 1)

# IOPub channel


def test_stream(test_code, result):
    flush_channels()

    msg_id, reply = execute(test_code)

    stdout = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(stdout, 'stream', msg_id)
    content = stdout['content']
    nt.assert_equal(content['text'], result)


def test_display_data(test_code, result):
    flush_channels()

    msg_id, reply = execute(test_code)
    
    display = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(display, 'display_data', parent=msg_id)
    data = display['content']['data']
    nt.assert_equal(data['text/plain'], result)

