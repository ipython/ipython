"""Tab-completion over zmq"""

# Trying to get print statements to work during completion, not very
# successfully...
from __future__ import print_function

import itertools
try:
    import readline
except ImportError:
    readline = None
import rlcompleter
import time

import session

class KernelCompleter(object):
    """Kernel-side completion machinery."""
    def __init__(self, namespace):
        self.namespace = namespace
        self.completer = rlcompleter.Completer(namespace)

    def complete(self, line, text):
        # We'll likely use linel later even if now it's not used for anything
        matches = []
        complete = self.completer.complete
        for state in itertools.count():
            comp = complete(text, state)
            if comp is None:
                break
            matches.append(comp)
        return matches
    

class ClientCompleter(object):
    """Client-side completion machinery.

    How it works: self.complete will be called multiple times, with
    state=0,1,2,... When state=0 it should compute ALL the completion matches,
    and then return them for each value of state."""
    
    def __init__(self, client, session, socket):
        # ugly, but we get called asynchronously and need access to some
        # client state, like backgrounded code
        assert readline is not None, "ClientCompleter depends on readline"
        self.client = client
        self.session = session
        self.socket = socket
        self.matches = []

    def request_completion(self, text):
        # Get full line to give to the kernel in case it wants more info.
        line = readline.get_line_buffer()
        # send completion request to kernel
        msg = self.session.send(self.socket,
                                'complete_request',
                                dict(text=text, line=line))

        # Give the kernel up to 0.5s to respond
        for i in range(5):
            ident,rep = self.session.recv(self.socket)
            rep = session.Message(rep)
            if rep is not None and rep.msg_type == 'complete_reply':
                matches = rep.content.matches
                break
            time.sleep(0.1)
        else:
            # timeout
            print ('TIMEOUT')  # Can't see this message...
            matches = None
        return matches
    
    def complete(self, text, state):
        
        if self.client.backgrounded > 0:
            print("\n[Not completing, background tasks active]")
            print(readline.get_line_buffer(), end='')
            return None
        
        if state==0:
            matches = self.request_completion(text)
            if matches is None:
                self.matches = []
                print('WARNING: Kernel timeout on tab completion.')
            else:
                self.matches = matches

        try:
            return self.matches[state]
        except IndexError:
            return None
