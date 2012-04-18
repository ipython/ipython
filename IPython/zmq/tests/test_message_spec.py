"""Test suite for our zeromq-based messaging specification.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

import re
import sys
import time
from subprocess import PIPE
from Queue import Empty

import nose.tools as nt

from ..blockingkernelmanager import BlockingKernelManager

from IPython.utils import io
from IPython.utils.traitlets import (
    HasTraits, TraitError, Bool, Unicode, Dict, Integer, List, Enum,
)

#-----------------------------------------------------------------------------
# Global setup and utilities
#-----------------------------------------------------------------------------

def setup():
    global KM
    KM = BlockingKernelManager()

    KM.start_kernel(stdout=PIPE, stderr=PIPE)
    KM.start_channels()

def teardown():
    KM.stop_channels()
    KM.shutdown_kernel()

def flush_channels():
    """flush any messages waiting on the queue"""
    for channel in (KM.shell_channel, KM.sub_channel):
        for msg in channel.get_msgs():
            validate_message(msg)
    
def flush(f):
    """decorator for flushing any incoming messages unhandled after the test"""

    def wrapped(*args, **kwargs):
        result = f(*args, **kwargs)
        flush_channels()
        return result

    return wrapped

def flush_busy_pyin(msg_id=None):
    """flush status=busy / pyin messages"""

def execute(code='', **kwargs):
    """wrapper for doing common steps for validating an execution request"""
    shell = KM.shell_channel
    sub = KM.sub_channel
    
    msg_id = shell.execute(code=code, **kwargs)
    reply = shell.get_msg(timeout=2)
    validate_message(reply, 'execute_reply', msg_id)
    busy = sub.get_msg(timeout=2)
    validate_message(busy, 'status', msg_id)
    nt.assert_equals(busy['content']['execution_state'], 'busy')
    
    if not kwargs.get('silent'):
        pyin = sub.get_msg(timeout=2)
        validate_message(pyin, 'pyin', msg_id)
        nt.assert_equals(pyin['content']['code'], code)
    
    return msg_id, reply['content']

#-----------------------------------------------------------------------------
# MSG Spec References
#-----------------------------------------------------------------------------


class Reference(HasTraits):
    
    def check(self, d):
        """validate a dict against our traits"""
        for key in self.trait_names():
            nt.assert_true(key in d, "Missing key: %r, should be found in %s" % (key, d))
            # FIXME: always allow None, probably not a good idea
            if d[key] is None:
                continue
            try:
                setattr(self, key, d[key])
            except TraitError as e:
                nt.assert_true(False, str(e))


class RMessage(Reference):
    msg_id = Unicode()
    msg_type = Unicode()
    header = Dict()
    parent_header = Dict()
    content = Dict()

class RHeader(Reference):
    msg_id = Unicode()
    msg_type = Unicode()
    session = Unicode()
    username = Unicode()

class RContent(Reference):
    status = Enum((u'ok', u'error'))


class ExecuteReply(Reference):
    execution_count = Integer()
    status = Enum((u'ok', u'error'))
    
    def check(self, d):
        Reference.check(self, d)
        if d['status'] == 'ok':
            ExecuteReplyOkay().check(d)
        elif d['status'] == 'error':
            ExecuteReplyError().check(d)


class ExecuteReplyOkay(Reference):
    payload = List(Dict)
    user_variables = Dict()
    user_expressions = Dict()


class ExecuteReplyError(Reference):
    ename = Unicode()
    evalue = Unicode()
    traceback = List(Unicode)


class OInfoReply(Reference):
    name = Unicode()
    found = Bool()
    ismagic = Bool()
    isalias = Bool()
    namespace = Enum((u'builtin', u'magics', u'alias', u'Interactive'))
    type_name = Unicode()
    string_form = Unicode()
    base_class = Unicode()
    length = Integer()
    file = Unicode()
    definition = Unicode()
    argspec = Dict()
    init_definition = Unicode()
    docstring = Unicode()
    init_docstring = Unicode()
    class_docstring = Unicode()
    call_def = Unicode()
    call_docstring = Unicode()
    source = Unicode()
    
    def check(self, d):
        Reference.check(self, d)
        if d['argspec'] is not None:
            ArgSpec().check(d['argspec'])


class ArgSpec(Reference):
    args = List(Unicode)
    varargs = Unicode()
    varkw = Unicode()
    defaults = List(Unicode)


class Status(Reference):
    execution_state = Enum((u'busy', u'idle'))


class CompleteReply(Reference):
    matches = List(Unicode)


# IOPub messages

class PyIn(Reference):
    code = Unicode()


PyErr = ExecuteReplyError


class Stream(Reference):
    name = Enum((u'stdout', u'stderr'))
    data = Unicode()


mime_pat = re.compile(r'\w+/\w+')

class DisplayData(Reference):
    source = Unicode()
    metadata = Dict()
    data = Dict()
    def _data_changed(self, name, old, new):
        for k,v in new.iteritems():
            nt.assert_true(mime_pat.match(k))
            nt.assert_true(isinstance(v, basestring), "expected string data, got %r" % v)


references = {
    'execute_reply' : ExecuteReply(),
    'object_info_reply' : OInfoReply(),
    'status' : Status(),
    'complete_reply' : CompleteReply(),
    'pyin' : PyIn(),
    'pyerr' : PyErr(),
    'stream' : Stream(),
    'display_data' : DisplayData(),
}


def validate_message(msg, msg_type=None, parent=None):
    """validate a message"""
    RMessage().check(msg)
    if msg_type:
        nt.assert_equals(msg['msg_type'], msg_type)
    if parent:
        nt.assert_equal(msg['parent_header']['msg_id'], parent)
    content = msg['content']
    ref = references[msg['msg_type']]
    ref.check(content)


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

# Shell channel

def test_execute():
    shell = KM.shell_channel
    msg_id = shell.execute(code='x=1')
    reply = shell.get_msg(timeout=2)
    validate_message(reply, 'execute_reply', msg_id)
    
    flush_channels()


def test_execute_silent():
    msg_id, reply = execute(code='x=1', silent=True)
    
    # flush status=idle
    status = KM.sub_channel.get_msg(timeout=2)
    validate_message(status, 'status', msg_id)
    nt.assert_equals(status['content']['execution_state'], 'idle')

    nt.assert_raises(Empty, KM.sub_channel.get_msg, timeout=0.1)
    count = reply['execution_count']
    
    msg_id, reply = execute(code='x=2', silent=True)
    
    # flush status=idle
    status = KM.sub_channel.get_msg(timeout=2)
    validate_message(status, 'status', msg_id)
    nt.assert_equals(status['content']['execution_state'], 'idle')
    
    nt.assert_raises(Empty, KM.sub_channel.get_msg, timeout=0.1)
    count_2 = reply['execution_count']
    nt.assert_equals(count_2, count)
    
    flush_channels()


def test_execute_error():
    
    msg_id, reply = execute(code='1/0')
    nt.assert_equals(reply['status'], 'error')
    nt.assert_equals(reply['ename'], 'ZeroDivisionError')
    
    pyerr = KM.sub_channel.get_msg(timeout=2)
    validate_message(pyerr, 'pyerr', msg_id)
    
    flush_channels()


def test_execute_inc():
    """execute request should increment execution_count"""
    msg_id, reply = execute(code='x=1')
    count = reply['execution_count']
    
    flush_channels()
    
    msg_id, reply = execute(code='x=2')
    count_2 = reply['execution_count']
    nt.assert_equals(count_2, count+1)
    
    flush_channels()


def test_user_variables():
    msg_id, reply = execute(code='x=1', user_variables=['x'])
    user_variables = reply['user_variables']
    nt.assert_equals(user_variables, {u'x' : u'1'})
    
    flush_channels()


def test_user_expressions():
    msg_id, reply = execute(code='x=1', user_expressions=dict(foo='x+1'))
    user_expressions = reply['user_expressions']
    nt.assert_equals(user_expressions, {u'foo' : u'2'})
    
    flush_channels()


def test_oinfo():
    shell = KM.shell_channel
    
    msg_id = shell.object_info('a')
    reply = shell.get_msg(timeout=2)
    validate_message(reply, 'object_info_reply', msg_id)
    
    flush_channels()


def test_oinfo_found():
    shell = KM.shell_channel

    msg_id, reply = execute(code='a=5')
    
    msg_id = shell.object_info('a')
    reply = shell.get_msg(timeout=2)
    validate_message(reply, 'object_info_reply', msg_id)
    content = reply['content']
    nt.assert_true(content['found'])
    
    flush_channels()


def test_oinfo_detail():
    shell = KM.shell_channel

    msg_id, reply = execute(code='ip=get_ipython()')

    msg_id = shell.object_info('ip.object_inspect', detail_level=2)
    reply = shell.get_msg(timeout=2)
    validate_message(reply, 'object_info_reply', msg_id)
    content = reply['content']
    nt.assert_true(content['found'])

    flush_channels()


def test_oinfo_not_found():
    shell = KM.shell_channel

    msg_id = shell.object_info('dne')
    reply = shell.get_msg(timeout=2)
    validate_message(reply, 'object_info_reply', msg_id)
    content = reply['content']
    nt.assert_false(content['found'])

    flush_channels()


def test_complete():
    shell = KM.shell_channel
    
    msg_id, reply = execute(code="alpha = albert = 5")
    
    msg_id = shell.complete('al', 'al', 2)
    reply = shell.get_msg(timeout=2)
    validate_message(reply, 'complete_reply', msg_id)
    matches = reply['content']['matches']
    for name in ('alpha', 'albert'):
        nt.assert_true(name in matches, "Missing match: %r" % name)
    
    flush_channels()


def test_stream():
    msg_id, reply = execute("print('hi')")

    stdout = KM.sub_channel.get_msg(timeout=2)
    validate_message(stdout, 'stream', msg_id)
    content = stdout['content']
    nt.assert_equals(content['name'], u'stdout')
    nt.assert_equals(content['data'], u'hi\n')
    
    flush_channels()


def test_display():
    
    msg_id, reply = execute("from IPython.core.display import display; display(1)")
    
    display = KM.sub_channel.get_msg(timeout=2)
    validate_message(display, 'display_data', parent=msg_id)
    data = display['content']['data']
    nt.assert_equals(data['text/plain'], u'1')
    
    flush_channels()

    