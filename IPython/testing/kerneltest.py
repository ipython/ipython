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

from messagespec import *

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

