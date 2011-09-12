import __builtin__
import sys
from base64 import encodestring

from IPython.core.displayhook import DisplayHook
from IPython.utils.traitlets import Instance, Dict
from session import extract_header, Session

class ZMQDisplayHook(object):
    """A simple displayhook that publishes the object's repr over a ZeroMQ
    socket."""
    topic=None

    def __init__(self, session, pub_socket):
        self.session = session
        self.pub_socket = pub_socket
        self.parent_header = {}

    def __call__(self, obj):
        if obj is None:
            return

        __builtin__._ = obj
        sys.stdout.flush()
        sys.stderr.flush()
        msg = self.session.send(self.pub_socket, u'pyout', {u'data':repr(obj)},
                               parent=self.parent_header, ident=self.topic)

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)


def _encode_binary(format_dict):
    pngdata = format_dict.get('image/png')
    if pngdata is not None:
        format_dict['image/png'] = encodestring(pngdata).decode('ascii')
    jpegdata = format_dict.get('image/jpeg')
    if jpegdata is not None:
        format_dict['image/jpeg'] = encodestring(jpegdata).decode('ascii')


class ZMQShellDisplayHook(DisplayHook):
    """A displayhook subclass that publishes data using ZeroMQ. This is intended
    to work with an InteractiveShell instance. It sends a dict of different
    representations of the object."""

    session = Instance(Session)
    pub_socket = Instance('zmq.Socket')
    parent_header = Dict({})

    def set_parent(self, parent):
        """Set the parent for outbound messages."""
        self.parent_header = extract_header(parent)

    def start_displayhook(self):
        self.msg = self.session.msg(u'pyout', {}, parent=self.parent_header)

    def write_output_prompt(self):
        """Write the output prompt."""
        if self.do_full_cache:
            self.msg['content']['execution_count'] = self.prompt_count

    def write_format_data(self, format_dict):
        _encode_binary(format_dict)
        self.msg['content']['data'] = format_dict

    def finish_displayhook(self):
        """Finish up all displayhook activities."""
        sys.stdout.flush()
        sys.stderr.flush()
        self.session.send(self.pub_socket, self.msg)
        self.msg = None

