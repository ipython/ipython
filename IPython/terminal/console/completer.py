# -*- coding: utf-8 -*-
"""Adapt readline completer interface to make ZMQ request."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

from IPython.config import Configurable
from IPython.core.completer import IPCompleter
from IPython.utils.py3compat import str_to_unicode, unicode_to_str, cast_bytes, cast_unicode
from IPython.utils.traitlets import Float
import IPython.utils.rlineimpl as readline

class ZMQCompleter(IPCompleter):
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
        # don't do any splitting client-side,
        # rely on the kernel for that
        self.splitter.delims = '\r\n'
        if self.readline:
            self.readline.set_completer_delims('\r\n')
    
    def complete_request(self, text):
        line = str_to_unicode(readline.get_line_buffer())
        byte_cursor_pos = readline.get_endidx()
        
        # get_endidx is a byte offset
        # account for multi-byte characters to get correct cursor_pos
        bytes_before_cursor = cast_bytes(line)[:byte_cursor_pos]
        cursor_pos = len(cast_unicode(bytes_before_cursor))
        
        # send completion request to kernel
        # Give the kernel up to 5s to respond
        msg_id = self.client.complete(
            code=line,
            cursor_pos=cursor_pos,
        )
    
        msg = self.client.shell_channel.get_msg(timeout=self.timeout)
        if msg['parent_header']['msg_id'] == msg_id:
            content = msg['content']
            cursor_start = content['cursor_start']
            matches = [ line[:cursor_start] + m for m in content['matches'] ]
            if content["cursor_end"] < cursor_pos:
                extra = line[content["cursor_end"]: cursor_pos]
                matches = [m + extra for m in matches]
            matches = [ unicode_to_str(m) for m in matches ]
            return matches
        return []
    
    def rlcomplete(self, text, state):
        if state == 0:
            try:
                self.matches = self.complete_request(text)
            except Empty:
                #print('WARNING: Kernel timeout on tab completion.')
                pass
        
        try:
            return self.matches[state]
        except IndexError:
            return None
    
    def complete(self, text, line, cursor_pos=None):
        return self.rlcomplete(text, 0)
