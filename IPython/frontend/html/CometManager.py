"""Manages messages for Comet design pattern

COMET design pattern:
http://en.wikipedia.org/wiki/Comet_(programming)

Basic idea -- webpage asks server via a GET request. Server blocks until
something is available, then sends it along to waiting client.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import time
import Queue

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------
# seconds without heartbeat that client considered dead
client_death = 300 

class Manager(object):
    """Tracks msg_id, client get requests for the Comet design pattern"""
    def __init__(self):
        self.clients = {}
        self.req_queue = Queue.Queue()
        
    def register(self, client_id):
        self.clients[client_id] = [time.time(), Queue.Queue()]
    
    def __getitem__(self, client_id):
        if client_id in self.clients:
            return self.clients[client_id][1]
        else:
            return None
    
    def append(self, msg):
        """Add a message to the queues across all tracked clients"""
        for i in self.clients.keys():
            dead_for = time.time() - self.clients[i][0]
            #Remove client if no heartbeat, otherwise add to its queue
            if dead_for > client_death:
                del self.clients[i]
            else:
                self.clients[i][1].put(msg)
    
    def __contains__(self, client_id):
        return client_id in self.clients
    
    def heartbeat(self, client_id):
        """Updates the client heartbeat"""
        if client_id in self.clients:
            self.clients[client_id][0] = time.time()
            
    def connect(self):
        #FIXME: better connect method to return execution_count without COMET
        return self.kernel_manager.xreq_channel.execute("")
        
    def execute(self, *args):
        return self.kernel_manager.xreq_channel.execute(*args)
    
    def complete(self, code, pos):
        chunk = re.split('\s|\(|=|;', code[:int(pos)])[-1]
        self.kernel_manager.xreq_channel.complete(chunk, code, pos)
        return self.req_queue.get()
    
    def inspect(self, oname):
        self.kernel_manager.xreq_channel.object_info(oname)
        return self.req_queue.get()
    
    def history(self, index = None, raw = False, output=False):
        if index == -1:
            index = None
            
        self.kernel_manager.xreq_channel.history(index, raw, output)
        return self.req_queue.get()
            
    def addreq(self, msg):
        """Adds a message to the immediate-return queue
        """
        self.req_queue.put(msg)
