"""Replacements for sys.displayhook that publish over ZMQ."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys

from IPython.core.displayhook import DisplayHook
from IPython.kernel.inprocess.socket import SocketABC
from IPython.utils.jsonutil import encode_images
from IPython.utils.py3compat import builtin_mod
from IPython.utils.traitlets import Instance, Dict
from .session import extract_header, Session

class ZMQDisplayHook(object):
    """A simple displayhook that publishes the object's repr over a ZeroMQ
    socket."""
    topic=b'execute_result'

    def __init__(self, session, pub_socket):
        self.session = session
        self.pub_socket = pub_socket
        self.parent_header = {}

    def __call__(self, obj):
        if obj is None:
            return

        builtin_mod._ = obj
        sys.stdout.flush()
        sys.stderr.flush()
        msg = self.session.send(self.pub_socket, u'execute_result', {u'data':repr(obj)},
                               parent=self.parent_header, ident=self.topic)

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)


class ZMQShellDisplayHook(DisplayHook):
    """A displayhook subclass that publishes data using ZeroMQ. This is intended
    to work with an InteractiveShell instance. It sends a dict of different
    representations of the object."""
    topic=None

    session = Instance(Session)
    pub_socket = Instance(SocketABC)
    parent_header = Dict({})

    def set_parent(self, parent):
        """Set the parent for outbound messages."""
        self.parent_header = extract_header(parent)

    def start_displayhook(self):
        self.msg = self.session.msg(u'execute_result', {
            'data': {},
            'metadata': {},
        }, parent=self.parent_header)

    def write_output_prompt(self):
        """Write the output prompt."""
        self.msg['content']['execution_count'] = self.prompt_count

    def write_format_data(self, format_dict, md_dict=None):
        self.msg['content']['data'] = encode_images(format_dict)
        self.msg['content']['metadata'] = md_dict

    def finish_displayhook(self):
        """Finish up all displayhook activities."""
        sys.stdout.flush()
        sys.stderr.flush()
        if self.msg['content']['data']:
            self.session.send(self.pub_socket, self.msg, ident=self.topic)
        self.msg = None

