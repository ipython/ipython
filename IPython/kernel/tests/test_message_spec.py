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
                assert False, str(e)


class Version(Unicode):
    def __init__(self, *args, **kwargs):
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)
        kwargs['default_value'] = self.min
        super(Version, self).__init__(*args, **kwargs)
    
    def validate(self, obj, value):
        if self.min and V(value) < V(self.min):
            raise TraitError("bad version: %s < %s" % (value, self.min))
        if self.max and (V(value) > V(self.max)):
            raise TraitError("bad version: %s > %s" % (value, self.max))


class RMessage(Reference):
    msg_id = Unicode()
    msg_type = Unicode()
    header = Dict()
    parent_header = Dict()
    content = Dict()
    
    def check(self, d):
        super(RMessage, self).check(d)
        RHeader().check(self.header)
        if self.parent_header:
            RHeader().check(self.parent_header)

class RHeader(Reference):
    msg_id = Unicode()
    msg_type = Unicode()
    session = Unicode()
    username = Unicode()
    version = Version(min='5.0')

mime_pat = re.compile(r'^[\w\-\+\.]+/[\w\-\+\.]+$')

class MimeBundle(Reference):
    metadata = Dict()
    data = Dict()
    def _data_changed(self, name, old, new):
        for k,v in iteritems(new):
            assert mime_pat.match(k)
            nt.assert_is_instance(v, string_types)

# shell replies

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
    user_expressions = Dict()


class ExecuteReplyError(Reference):
    ename = Unicode()
    evalue = Unicode()
    traceback = List(Unicode)


class InspectReply(MimeBundle):
    found = Bool()


class ArgSpec(Reference):
    args = List(Unicode)
    varargs = Unicode()
    varkw = Unicode()
    defaults = List()


class Status(Reference):
    execution_state = Enum((u'busy', u'idle', u'starting'))


class CompleteReply(Reference):
    matches = List(Unicode)
    cursor_start = Integer()
    cursor_end = Integer()
    status = Unicode()

class LanguageInfo(Reference):
    name = Unicode('python')
    version = Unicode(sys.version.split()[0])

class KernelInfoReply(Reference):
    protocol_version = Version(min='5.0')
    implementation = Unicode('ipython')
    implementation_version = Version(min='2.1')
    language_info = Dict()
    banner = Unicode()
    
    def check(self, d):
        Reference.check(self, d)
        LanguageInfo().check(d['language_info'])


class IsCompleteReply(Reference):
    status = Enum((u'complete', u'incomplete', u'invalid', u'unknown'))
    
    def check(self, d):
        Reference.check(self, d)
        if d['status'] == 'incomplete':
            IsCompleteReplyIncomplete().check(d)

class IsCompleteReplyIncomplete(Reference):
    indent = Unicode()


# IOPub messages

class ExecuteInput(Reference):
    code = Unicode()
    execution_count = Integer()


Error = ExecuteReplyError


class Stream(Reference):
    name = Enum((u'stdout', u'stderr'))
    text = Unicode()


class DisplayData(MimeBundle):
    pass


class ExecuteResult(MimeBundle):
    execution_count = Integer()

class HistoryReply(Reference):
    history = List(List())


references = {
    'execute_reply' : ExecuteReply(),
    'inspect_reply' : InspectReply(),
    'status' : Status(),
    'complete_reply' : CompleteReply(),
    'kernel_info_reply': KernelInfoReply(),
    'is_complete_reply': IsCompleteReply(),
    'execute_input' : ExecuteInput(),
    'execute_result' : ExecuteResult(),
    'history_reply' : HistoryReply(),
    'error' : Error(),
    'stream' : Stream(),
    'display_data' : DisplayData(),
    'header' : RHeader(),
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

def test_execute_stop_on_error():
    """execute request should not abort execution queue with stop_on_error False"""
    flush_channels()
    
    fail = '\n'.join([
        # sleep to ensure subsequent message is waiting in the queue to be aborted
        'import time',
        'time.sleep(0.5)',
        'raise ValueError',
    ])
    KC.execute(code=fail)
    msg_id = KC.execute(code='print("Hello")')
    KC.get_shell_msg(timeout=TIMEOUT)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    nt.assert_equal(reply['content']['status'], 'aborted')

    flush_channels()

    KC.execute(code=fail, stop_on_error=False)
    msg_id = KC.execute(code='print("Hello")')
    KC.get_shell_msg(timeout=TIMEOUT)
    reply = KC.get_shell_msg(timeout=TIMEOUT)
    nt.assert_equal(reply['content']['status'], 'ok')


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
    nt.assert_in('Signature:', text)
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

