# -*- coding: utf-8 -*-
import readline
import time
import sys
stdout = sys.stdout
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
        #msg_id = self.km.xreq_channel.complete(text=text,line=line)#this method is not working, the code not continue
	msg = self.km.session.send(self.km.xreq_channel.socket,
                                'complete_request',
                                dict(text=text, line=line))
        # send completion request to kernel
        # Give the kernel up to 0.5s to respond
        msg_matches = None
        for i in range(5):
	   if self.km.xreq_channel.was_called():
	      msg_xreq =  self.km.xreq_channel.get_msg()
	      if msg["header"]['session'] == msg_xreq["parent_header"]['session'] :
		 if msg_xreq["content"]["status"] == 'ok' :
		    if msg_xreq["msg_type"] == "complete_reply" :
		       msg_matches = msg_xreq["content"]["matches"]
		       #break
           time.sleep(0.1)
        return msg_matches   
    
    def complete(self, text, state):
        if state == 0 :
	   self.matches = self.complete_request(text)
	   
        if self.matches is None:
           self.matches = []
           print('WARNING: Kernel timeout on tab completion.')
        #print self.matches
	try:
	    return self.matches[state]
	except IndexError:
	    return None
        
        
        
