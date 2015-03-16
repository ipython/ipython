"""A simple tool to test the ZMQ kernel by publishing messages and checking the response."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import, print_function

import atexit
import json
import sys
from importlib import import_module

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

import nose.tools as nt

from IPython.kernel import manager

from IPython.testing.messagespec_common import *

#-------------------------------------------------------------------------
# Globals
#-------------------------------------------------------------------------

STARTUP_TIMEOUT = 60
TIMEOUT = 15

KM = None
KC = None
validate_message = None

#-------------------------------------------------------------------------
# Code to setup the kernel for testing
#-------------------------------------------------------------------------


def start_new_kernel(kernel='python', **kwargs):
    """start a new kernel, and return its Manager and Client
    """
    return manager.start_new_kernel(startup_timeout=STARTUP_TIMEOUT, kernel_name=kernel, **kwargs)


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


def check_execute(test_code):
    flush_channels()

    msg_id = KC.execute(code=test_code)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'execute_reply', msg_id)
    return reply


def check_user_expressions(test_code, user_expression):
    flush_channels()

    msg_id, reply = execute(
        code=test_code, user_expressions=dict(foo=user_expression))
    user_expressions = reply['user_expressions']
    return user_expressions


def check_oinfo(inspect_object):
    flush_channels()

    msg_id = KC.inspect(inspect_object)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'inspect_reply', msg_id)
    return reply


def check_complete(test_code):
    flush_channels()

    msg_id = KC.complete(test_code, 2)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'complete_reply', msg_id)
    return reply


def check_kernel_info():
    flush_channels()

    msg_id = KC.kernel_info()
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    # Do not validate because kernel info versions will be different
    # for each kernel - leave it to developer to check the result
    #validate_message(reply, 'kernel_info_reply', msg_id)
    return reply


def check_single_payload(test_code):
    flush_channels()
    msg_id, reply = execute(code=test_code)
    payload = reply['payload']
    return payload


def check_is_complete(test_code):
    flush_channels()

    msg_id = KC.is_complete(test_code)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'is_complete_reply', msg_id)
    return reply


# The below 3 history tests are run for the last one command and
# with a .* pattern so that we only check the test code. This is 
# enough to validate all the parts of the message spec

def check_history_range(test_code):
    flush_channels()

    msg_id_exec = KC.execute(code=test_code, store_history=True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)

    msg_id = KC.history(
        hist_access_type='range', raw=True, output=True, start=1, stop=2, session=0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    return content


def check_history_tail(test_code):
    flush_channels()

    msg_id_exec = KC.execute(code=test_code, store_history=True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)

    msg_id = KC.history(
        hist_access_type='tail', raw=True, output=True, n=1, session=0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    return content


def check_history_search(test_code):
    flush_channels()

    msg_id_exec = KC.execute(code=test_code, store_history=True)
    reply_exec = KC.get_shell_msg(timeout=TIMEOUT)

    msg_id = KC.history(
        hist_access_type='search', raw=True, output=True, n=1, pattern='.*', session=0)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'history_reply', msg_id)
    content = reply['content']
    return content

# IOPub channel


def check_stream(test_code):
    flush_channels()

    msg_id, reply = execute(test_code)

    stdout = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(stdout, 'stream', msg_id)
    content = stdout['content']
    return content


def check_display_data(test_code):
    flush_channels()

    msg_id, reply = execute(test_code)

    display = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(display, 'display_data', parent=msg_id)
    data = display['content']['data']
    return data

# Mapping of message types, check methods and the parameters needed.
# The test runner will validate the number of parameters based on 
# the params list and not run any check which does not have all the
# parameters. This keeps the design flexibale to add more message
# types easily
checks = {
    'execute': {"f": check_execute, "params": ["test_code"]},
    'user_expressions': {"f": check_user_expressions, "params": ["test_code", "user_expression"]},
    'oinfo': {"f": check_oinfo, "params": ["inspect_object"]},
    'complete': {"f": check_complete, "params": ["test_code"]},
    'kernel_info': {"f": check_kernel_info, "params": []},
    'single_payload': {"f": check_single_payload, "params": ["test_code"]},
    'is_complete': {"f": check_is_complete, "params": ["test_code"]},
    'history_range': {"f": check_history_range, "params": ["test_code"]},
    'history_tail': {"f": check_history_tail, "params": ["test_code"]},
    'history_search': {"f": check_history_search, "params": ["test_code"]},
    'stream': {"f": check_stream, "params": ["test_code"]},
    'display_data': {"f": check_display_data, "params": ["test_code"]},
}


#takes one message type, gets the params and runs the check
def run_test(message, data):
    test_info = checks[message]
    f = test_info["f"]
    params = test_info["params"]
    args = []
    missing = [param for param in params if param not in data]
    if params.__len__() > 0 and missing.__len__() > 0:
        print("Missing parameters for test %s. Missing parameters - %s\n" %
              (message, missing))
        return
    else:
        args = [data[param] for param in params]
    return f(*args)

#load the json script and run through the tests
def run_defined_tests(kernel, test_file,spec_version):

    global KC, KM, validate_message
    
    #get the validator and import the spec
    validate_message = get_message_spec_validator(spec_version)
    
    if KC is None:
        start_global_kernel(kernel)

    with open(test_file, 'r') as test_script:
        tests = json.loads(test_script.read())
        for key in tests.keys():
            data = tests[key]
            print("Running test for %s with data %s\n" % (key, data))
            result = run_test(key, data)
            print("Test returned - %s\n" % (result,))

# method to get the correct message spec version for the test
def get_message_spec_validator(spec_version):
    
    """
    
    For now there is only one version of the message specification that can be tested.
    As more versions are added this will be expanded to import the correct version to 
    be used for the kernel tests.
    
    The choice will be made based on spec_version
    
    Every version of message spec should implement a validation method that takes 3
    parameters message, message type and a parent. The message type and parent are
    optional for validation.
    
    """
    spec_module = import_module('IPython.testing.messagespec')
    return spec_module.validate_message

def main():
    
    args = sys.argv[1:]
    if args.__len__() < 2:
        print('Usage: python kerneltest.py <kernel name> <test script file> <optional message spec version>')
        print('\nIf no messsage spec version is specified then vresion 5 is assumed.')
        print('\nTest script format : \n{\n\t<message type>:{\n\t\tparam_1_name:param_1_value,.....\n\t}\n}')
        print('\nSupported message types \n%s'%(checks.keys()))
    else:
        if(args.__len__() == 3):
            spec_version = args[2]
        else:
            spec_version = 5
        
        print("Using kernel %s and test script %s. Message spec version %s\n\n"%(args[0],args[1],spec_version))
        run_defined_tests(args[0],args[1],spec_version)

if __name__=='__main__':
    main()