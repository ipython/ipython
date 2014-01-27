"""Adapt readline completer interface to make ZMQ request.
"""
# -*- coding: utf-8 -*-
try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

from IPython.config import Configurable
from IPython.utils.traitlets import Float

class ZMQCompleter(Configurable):
    """Client-side completion machinery.

    How it works: self.complete will be called multiple times, with
    state=0,1,2,... When state=0 it should compute ALL the completion matches,
    and then return them for each value of state."""

    timeout = Float(5.0, config=True, help='timeout before completion abort')

    def __init__(self, shell, client, config=None):
        super(ZMQCompleter,self).__init__(config=config)

        self.shell = shell
        self.client =  client
        self.matches = []

    def _rl_get_lineinfo(self):
        import readline
        line = readline.get_line_buffer()
        cursor_pos = readline.get_endidx()
        return line, cursor_pos

    def rlcomplete_request(self, text):
        line, cursor_pos = self._rl_get_lineinfo()
        return complete_request(text, line, cursor_pos)

    def rlcomplete(self, text, state):
        line, cursor_pos = self._rl_get_lineinfo()
        return self.complete(text, line, cursor_pos, state)

    def complete_request(self, text, line, cursor_pos):
        # send completion request to kernel
        # Give the kernel up to 0.5s to respond
        msg_id = self.client.shell_channel.complete(text=text, line=line,
                                                        cursor_pos=cursor_pos)

        msg = self.client.shell_channel.get_msg(timeout=self.timeout)
        if msg['parent_header']['msg_id'] == msg_id:
            return msg['content']['matches']
        return []

    def complete(self, text, line, cursor_pos=None, state=0):
        if state == 0:
            try:
                self.matches = self.complete_request(text, line, cursor_pos)
            except Empty:
                #print('WARNING: Kernel timeout on tab completion.')
                pass

        try:
            return self.matches[state]
        except IndexError:
            return None
