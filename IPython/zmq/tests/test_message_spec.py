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
from .. import ipkernel


from IPython.testing import decorators as dec
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
    
    # wait for kernel to be ready
    KM.shell_channel.execute("pass")
    KM.shell_channel.get_msg(block=True, timeout=5)
    flush_channels()


def teardown():
    KM.stop_channels()
    KM.shutdown_kernel()


def flush_channels():
    """flush any messages waiting on the queue"""
    for channel in (KM.shell_channel, KM.sub_channel):
        while True:
            try:
                msg = channel.get_msg(block=True, timeout=0.1)
            except Empty:
                break
            else:
                list(validate_message(msg))


def execute(code='', **kwargs):
    """wrapper for doing common steps for validating an execution request"""
    shell = KM.shell_channel
    sub = KM.sub_channel
    
    msg_id = shell.execute(code=code, **kwargs)
    reply = shell.get_msg(timeout=2)
    list(validate_message(reply, 'execute_reply', msg_id))
    busy = sub.get_msg(timeout=2)
    list(validate_message(busy, 'status', msg_id))
    nt.assert_equal(busy['content']['execution_state'], 'busy')
    
    if not kwargs.get('silent'):
        pyin = sub.get_msg(timeout=2)
        list(validate_message(pyin, 'pyin', msg_id))
        nt.assert_equal(pyin['content']['code'], code)
    
    return msg_id, reply['content']

#-----------------------------------------------------------------------------
# MSG Spec References
#-----------------------------------------------------------------------------


class Reference(HasTraits):

    """
    Base class for message spec specification testing.

    This class is the core of the message specification test.  The
    idea is that child classes implement trait attributes for each
    message keys, so that message keys can be tested against these
    traits using :meth:`check` method.

    """

    def check(self, d):
        """validate a dict against our traits"""
        for key in self.trait_names():
            yield nt.assert_true(key in d, "Missing key: %r, should be found in %s" % (key, d))
            # FIXME: always allow None, probably not a good idea
            if d[key] is None:
                continue
            try:
                setattr(self, key, d[key])
            except TraitError as e:
                yield nt.assert_true(False, str(e))


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
        for tst in Reference.check(self, d):
            yield tst
        if d['status'] == 'ok':
            for tst in ExecuteReplyOkay().check(d):
                yield tst
        elif d['status'] == 'error':
            for tst in ExecuteReplyError().check(d):
                yield tst


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
        for tst in Reference.check(self, d):
            yield tst
        if d['argspec'] is not None:
            for tst in ArgSpec().check(d['argspec']):
                yield tst


class ArgSpec(Reference):
    args = List(Unicode)
    varargs = Unicode()
    varkw = Unicode()
    defaults = List()


class Status(Reference):
    execution_state = Enum((u'busy', u'idle'))


class CompleteReply(Reference):
    matches = List(Unicode)


class VersionReply(Reference):
    version = Enum((ipkernel.version))
    version_major = Enum((ipkernel.version_major,))
    version_minor = Enum((ipkernel.version_minor,))


# IOPub messages

class PyIn(Reference):
    code = Unicode()
    execution_count = Integer()


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


class PyOut(Reference):
    execution_count = Integer()
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
    'version_reply': VersionReply(),
    'pyin' : PyIn(),
    'pyout' : PyOut(),
    'pyerr' : PyErr(),
    'stream' : Stream(),
    'display_data' : DisplayData(),
}
"""
Specifications of `content` part of the reply messages.
"""


def validate_message(msg, msg_type=None, parent=None):
    """validate a message
    
    This is a generator, and must be iterated through to actually
    trigger each test.
    
    If msg_type and/or parent are given, the msg_type and/or parent msg_id
    are compared with the given values.
    """
    RMessage().check(msg)
    if msg_type:
        yield nt.assert_equal(msg['msg_type'], msg_type)
    if parent:
        yield nt.assert_equal(msg['parent_header']['msg_id'], parent)
    content = msg['content']
    ref = references[msg['msg_type']]
    for tst in ref.check(content):
        yield tst


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

# Shell channel

@dec.parametric
def test_execute():
    flush_channels()
    
    shell = KM.shell_channel
    msg_id = shell.execute(code='x=1')
    reply = shell.get_msg(timeout=2)
    for tst in validate_message(reply, 'execute_reply', msg_id):
        yield tst


@dec.parametric
def test_execute_silent():
    flush_channels()
    msg_id, reply = execute(code='x=1', silent=True)
    
    # flush status=idle
    status = KM.sub_channel.get_msg(timeout=2)
    for tst in validate_message(status, 'status', msg_id):
        yield tst
    nt.assert_equal(status['content']['execution_state'], 'idle')

    yield nt.assert_raises(Empty, KM.sub_channel.get_msg, timeout=0.1)
    count = reply['execution_count']
    
    msg_id, reply = execute(code='x=2', silent=True)
    
    # flush status=idle
    status = KM.sub_channel.get_msg(timeout=2)
    for tst in validate_message(status, 'status', msg_id):
        yield tst
    yield nt.assert_equal(status['content']['execution_state'], 'idle')
    
    yield nt.assert_raises(Empty, KM.sub_channel.get_msg, timeout=0.1)
    count_2 = reply['execution_count']
    yield nt.assert_equal(count_2, count)


@dec.parametric
def test_execute_error():
    flush_channels()
    
    msg_id, reply = execute(code='1/0')
    yield nt.assert_equal(reply['status'], 'error')
    yield nt.assert_equal(reply['ename'], 'ZeroDivisionError')
    
    pyerr = KM.sub_channel.get_msg(timeout=2)
    for tst in validate_message(pyerr, 'pyerr', msg_id):
        yield tst


def test_execute_inc():
    """execute request should increment execution_count"""
    flush_channels()

    msg_id, reply = execute(code='x=1')
    count = reply['execution_count']
    
    flush_channels()
    
    msg_id, reply = execute(code='x=2')
    count_2 = reply['execution_count']
    nt.assert_equal(count_2, count+1)


def test_user_variables():
    flush_channels()

    msg_id, reply = execute(code='x=1', user_variables=['x'])
    user_variables = reply['user_variables']
    nt.assert_equal(user_variables, {u'x' : u'1'})


def test_user_expressions():
    flush_channels()

    msg_id, reply = execute(code='x=1', user_expressions=dict(foo='x+1'))
    user_expressions = reply['user_expressions']
    nt.assert_equal(user_expressions, {u'foo' : u'2'})


@dec.parametric
def test_oinfo():
    flush_channels()

    shell = KM.shell_channel
    
    msg_id = shell.object_info('a')
    reply = shell.get_msg(timeout=2)
    for tst in validate_message(reply, 'object_info_reply', msg_id):
        yield tst


@dec.parametric
def test_oinfo_found():
    flush_channels()

    shell = KM.shell_channel
    
    msg_id, reply = execute(code='a=5')
    
    msg_id = shell.object_info('a')
    reply = shell.get_msg(timeout=2)
    for tst in validate_message(reply, 'object_info_reply', msg_id):
        yield tst
    content = reply['content']
    yield nt.assert_true(content['found'])
    argspec = content['argspec']
    yield nt.assert_true(argspec is None, "didn't expect argspec dict, got %r" % argspec)


@dec.parametric
def test_oinfo_detail():
    flush_channels()

    shell = KM.shell_channel
    
    msg_id, reply = execute(code='ip=get_ipython()')
    
    msg_id = shell.object_info('ip.object_inspect', detail_level=2)
    reply = shell.get_msg(timeout=2)
    for tst in validate_message(reply, 'object_info_reply', msg_id):
        yield tst
    content = reply['content']
    yield nt.assert_true(content['found'])
    argspec = content['argspec']
    yield nt.assert_true(isinstance(argspec, dict), "expected non-empty argspec dict, got %r" % argspec)
    yield nt.assert_equal(argspec['defaults'], [0])


@dec.parametric
def test_oinfo_not_found():
    flush_channels()

    shell = KM.shell_channel
    
    msg_id = shell.object_info('dne')
    reply = shell.get_msg(timeout=2)
    for tst in validate_message(reply, 'object_info_reply', msg_id):
        yield tst
    content = reply['content']
    yield nt.assert_false(content['found'])


@dec.parametric
def test_complete():
    flush_channels()

    shell = KM.shell_channel
    
    msg_id, reply = execute(code="alpha = albert = 5")
    
    msg_id = shell.complete('al', 'al', 2)
    reply = shell.get_msg(timeout=2)
    for tst in validate_message(reply, 'complete_reply', msg_id):
        yield tst
    matches = reply['content']['matches']
    for name in ('alpha', 'albert'):
        yield nt.assert_true(name in matches, "Missing match: %r" % name)


@dec.parametric
def test_version_request():
    flush_channels()

    shell = KM.shell_channel

    msg_id = shell.version()
    reply = shell.get_msg(timeout=2)
    for tst in validate_message(reply, 'version_reply', msg_id):
        yield tst


# IOPub channel


@dec.parametric
def test_stream():
    flush_channels()

    msg_id, reply = execute("print('hi')")

    stdout = KM.sub_channel.get_msg(timeout=2)
    for tst in validate_message(stdout, 'stream', msg_id):
        yield tst
    content = stdout['content']
    yield nt.assert_equal(content['name'], u'stdout')
    yield nt.assert_equal(content['data'], u'hi\n')


@dec.parametric
def test_display_data():
    flush_channels()

    msg_id, reply = execute("from IPython.core.display import display; display(1)")
    
    display = KM.sub_channel.get_msg(timeout=2)
    for tst in validate_message(display, 'display_data', parent=msg_id):
        yield tst
    data = display['content']['data']
    yield nt.assert_equal(data['text/plain'], u'1')

