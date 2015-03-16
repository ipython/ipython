"""The v5 message specification. This can be used in the tests to verify messages."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.testing.messagespec_common import *

# message and header formats specific to verion 5

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

# version shell replies

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


"""
Specifications of `content` part of the reply messages.
"""
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

#validation specific to this version of the message specification

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
