"""Test suite for our zeromq-based message specification.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

import re
from subprocess import PIPE
try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

import nose.tools as nt

from IPython.kernel import KernelManager

from IPython.utils.traitlets import (
    HasTraits, TraitError, Bool, Unicode, Dict, Integer, List, Enum, Any,
)
from IPython.utils.py3compat import string_types, iteritems

from .utils import TIMEOUT, start_global_kernel, flush_channels, execute

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
KC = None

def setup():
    global KC
    KC = start_global_kernel()

#-----------------------------------------------------------------------------
# Message Spec References
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
            nt.assert_in(key, d)
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
    defaults = List()


class Status(Reference):
    execution_state = Enum((u'busy', u'idle', u'starting'))


class CompleteReply(Reference):
    matches = List(Unicode)


def Version(num, trait=Integer):
    return List(trait, default_value=[0] * num, minlen=num, maxlen=num)


class KernelInfoReply(Reference):

    protocol_version = Version(2)
    ipython_version = Version(4, Any)
    language_version = Version(3)
    language = Unicode()

    def _ipython_version_changed(self, name, old, new):
        for v in new:
            assert isinstance(v, int) or isinstance(v, string_types), \
            'expected int or string as version component, got {0!r}'.format(v)


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
        for k,v in iteritems(new):
            assert mime_pat.match(k)
            nt.assert_is_instance(v, string_types)


class PyOut(Reference):
    execution_count = Integer()
    data = Dict()
    def _data_changed(self, name, old, new):
        for k,v in iteritems(new):
            assert mime_pat.match(k)
            nt.assert_is_instance(v, string_types)


references = {
    'execute_reply' : ExecuteReply(),
    'object_info_reply' : OInfoReply(),
    'status' : Status(),
    'complete_reply' : CompleteReply(),
    'kernel_info_reply': KernelInfoReply(),
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
        nt.assert_equal(msg['msg_type'], msg_type)
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
    
    pyerr = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(pyerr, 'pyerr', msg_id)


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
    nt.assert_equal(user_variables, {u'x': {
        u'status': u'ok',
        u'data': {u'text/plain': u'1'},
        u'metadata': {},
    }})


def test_user_variables_fail():
    flush_channels()

    msg_id, reply = execute(code='x=1', user_variables=['nosuchname'])
    user_variables = reply['user_variables']
    foo = user_variables['nosuchname']
    nt.assert_equal(foo['status'], 'error')
    nt.assert_equal(foo['ename'], 'KeyError')


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

    msg_id = KC.object_info('a')
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'object_info_reply', msg_id)


def test_oinfo_found():
    flush_channels()

    msg_id, reply = execute(code='a=5')
    
    msg_id = KC.object_info('a')
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'object_info_reply', msg_id)
    content = reply['content']
    assert content['found']
    argspec = content['argspec']
    nt.assert_is(argspec, None)


def test_oinfo_detail():
    flush_channels()

    msg_id, reply = execute(code='ip=get_ipython()')
    
    msg_id = KC.object_info('ip.object_inspect', detail_level=2)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'object_info_reply', msg_id)
    content = reply['content']
    assert content['found']
    argspec = content['argspec']
    nt.assert_is_instance(argspec, dict, "expected non-empty argspec dict, got %r" % argspec)
    nt.assert_equal(argspec['defaults'], [0])


def test_oinfo_not_found():
    flush_channels()

    msg_id = KC.object_info('dne')
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'object_info_reply', msg_id)
    content = reply['content']
    nt.assert_false(content['found'])


def test_complete():
    flush_channels()

    msg_id, reply = execute(code="alpha = albert = 5")
    
    msg_id = KC.complete('al', 'al', 2)
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


# IOPub channel


def test_stream():
    flush_channels()

    msg_id, reply = execute("print('hi')")

    stdout = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(stdout, 'stream', msg_id)
    content = stdout['content']
    nt.assert_equal(content['name'], u'stdout')
    nt.assert_equal(content['data'], u'hi\n')


def test_display_data():
    flush_channels()

    msg_id, reply = execute("from IPython.core.display import display; display(1)")
    
    display = KC.iopub_channel.get_msg(timeout=TIMEOUT)
    validate_message(display, 'display_data', parent=msg_id)
    data = display['content']['data']
    nt.assert_equal(data['text/plain'], u'1')

