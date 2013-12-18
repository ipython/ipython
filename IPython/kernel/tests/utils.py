"""utilities for testing IPython kernels"""

#-------------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import atexit

from contextlib import contextmanager
from subprocess import PIPE, STDOUT
try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

import nose
import nose.tools as nt

from IPython.kernel import KernelManager

#-------------------------------------------------------------------------------
# Globals
#-------------------------------------------------------------------------------

STARTUP_TIMEOUT = 60
TIMEOUT = 15

KM = None
KC = None

#-------------------------------------------------------------------------------
# code
#-------------------------------------------------------------------------------


def start_new_kernel(argv=None):
    """start a new kernel, and return its Manager and Client"""
    km = KernelManager()
    kwargs = dict(stdout=nose.iptest_stdstreams_fileno(), stderr=STDOUT)
    if argv:
        kwargs['extra_arguments'] = argv
    km.start_kernel(**kwargs)
    kc = km.client()
    kc.start_channels()
    
    msg_id = kc.kernel_info()
    kc.get_shell_msg(block=True, timeout=STARTUP_TIMEOUT)
    flush_channels(kc)
    return km, kc

def flush_channels(kc=None):
    """flush any messages waiting on the queue"""
    from .test_message_spec import validate_message
    
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
    from .test_message_spec import validate_message
    if kc is None:
        kc = KC
    msg_id = kc.execute(code=code, **kwargs)
    reply = kc.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'execute_reply', msg_id)
    busy = kc.get_iopub_msg(timeout=TIMEOUT)
    validate_message(busy, 'status', msg_id)
    nt.assert_equal(busy['content']['execution_state'], 'busy')
    
    if not kwargs.get('silent'):
        pyin = kc.get_iopub_msg(timeout=TIMEOUT)
        validate_message(pyin, 'pyin', msg_id)
        nt.assert_equal(pyin['content']['code'], code)
    
    return msg_id, reply['content']

def start_global_kernel():
    """start the global kernel (if it isn't running) and return its client"""
    global KM, KC
    if KM is None:
        KM, KC = start_new_kernel()
        atexit.register(stop_global_kernel)
    return KC

@contextmanager
def kernel():
    """Context manager for the global kernel instance
    
    Should be used for most kernel tests
    
    Returns
    -------
    kernel_client: connected KernelClient instance
    """
    yield start_global_kernel()

def uses_kernel(test_f):
    """Decorator for tests that use the global kernel"""
    def wrapped_test():
        with kernel() as kc:
            test_f(kc)
    wrapped_test.__doc__ = test_f.__doc__
    wrapped_test.__name__ = test_f.__name__
    return wrapped_test

def stop_global_kernel():
    """Stop the global shared kernel instance, if it exists"""
    global KM, KC
    KC.stop_channels()
    KC = None
    if KM is None:
        return
    KM.shutdown_kernel(now=True)
    KM = None

@contextmanager
def new_kernel(argv=None):
    """Context manager for a new kernel in a subprocess
    
    Should only be used for tests where the kernel must not be re-used.
    
    Returns
    -------
    kernel_client: connected KernelClient instance
    """
    km, kc = start_new_kernel(argv)
    try:
        yield kc
    finally:
        kc.stop_channels()
        km.shutdown_kernel(now=True)


def assemble_output(iopub):
    """assemble stdout/err from an execution"""
    stdout = ''
    stderr = ''
    while True:
        msg = iopub.get_msg(block=True, timeout=1)
        msg_type = msg['msg_type']
        content = msg['content']
        if msg_type == 'status' and content['execution_state'] == 'idle':
            # idle message signals end of output
            break
        elif msg['msg_type'] == 'stream':
            if content['name'] == 'stdout':
                stdout += content['data']
            elif content['name'] == 'stderr':
                stderr += content['data']
            else:
                raise KeyError("bad stream: %r" % content['name'])
        else:
            # other output, ignored
            pass
    return stdout, stderr

def wait_for_idle(kc):
    while True:
        msg = kc.iopub_channel.get_msg(block=True, timeout=1)
        msg_type = msg['msg_type']
        content = msg['content']
        if msg_type == 'status' and content['execution_state'] == 'idle':
            break
