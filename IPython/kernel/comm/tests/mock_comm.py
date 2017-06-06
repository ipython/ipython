"""Mock Comm object for testing"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.



from IPython.kernel.comm import Comm
from uuid import uuid4
from collections import namedtuple

Message = namedtuple('Message', ['data', 'metadata'])

class MockComm(Comm):
    def __init__(self, target_name='', data=None, comm_id=None, **kwargs):
        self.kwargs = kwargs
        self.target_name = target_name
        self.data = data
        self.messages = []
        if comm_id is not None:
            self.comm_id = comm_id
        else:
            self.comm_id = 'mock-comm-'+uuid4().hex
        self.open = True

    def send(self, data=None, metadata=None):
        m = Message(data, metadata)
        if self.open is True:
            self.messages.append(m)
        else:
            raise ValueError("Comm object is closed, but message sent: %s"%(m))

    def open(self, data=None, metadata=None):
        pass

    def close(self, data=None, metadata=None):
        self.open = False

    def on_close(self, callback):
        pass

    def on_msg(self, callback):
        self._msg_callback = callback

    def handle_close(self, msg):
        pass

    def handle_msg(self, msg):
        if self._msg_callback:
            self._msg_callback(msg)
