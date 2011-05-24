# -*- coding: utf-8 -*-
import readline
from Queue import Empty

class ClientCompleter2p(object):
    """Client-side completion machinery.

    How it works: self.complete will be called multiple times, with
    state=0,1,2,... When state=0 it should compute ALL the completion matches,
    and then return them for each value of state."""
    
    def __init__(self,client, km):
        self.km =  km
        self.matches = []
        self.client = client
        
    def complete_request(self,text):
        line = readline.get_line_buffer()
        cursor_pos = readline.get_endidx()
        
        # send completion request to kernel
        # Give the kernel up to 0.5s to respond
        msg_id = self.km.xreq_channel.complete(text=text, line=line,
                                                        cursor_pos=cursor_pos)
        
        msg_xreq = self.km.xreq_channel.get_msg(timeout=0.5)
        if msg_xreq['parent_header']['msg_id'] == msg_id:
            return msg_xreq["content"]["matches"]
        return []
    
    def complete(self, text, state):
        if state == 0:
            try:
                self.matches = self.complete_request(text)
            except Empty:
                print('WARNING: Kernel timeout on tab completion.')
        
        try:
            return self.matches[state]
        except IndexError:
            return None
