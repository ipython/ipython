""" Defines a KernelManager that provides signals and slots.
"""

import os
import re
import cgi
import time
import json
import Queue
import threading
import mimetypes
from string import Template
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

client_death = 300 # seconds without heartbeat that client considered dead
#Base path to serve js and css files from
basepath = os.path.split(__file__)[0]+"/" 

class CometManager(object):
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
        if client_id in self.clients:
            self.clients[client_id][0] = time.time()
            
    def connect(self):
        return self.kernel_manager.xreq_channel.execute(*args)
        
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
        self.req_queue.put(msg)
        
manager = CometManager()

class IPyHttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        #Path is either a real path, or the client_id
        path = self.path.strip("/")
        if path in manager:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            #Manager.get blocks until a message is available
            json.dump(manager[path].get(), self.wfile)
        elif path == "notebook":
            self.send_response(200)
            self.send_header("Content-type", "application/xhtml+xml")
            self.end_headers()
            
            #This is a good spot to add login mechanics
            client_id = str(time.time())
            manager.register(client_id)
            page_text = Template(open(basepath + "notebook.html").read())
            
            self.wfile.write(page_text.safe_substitute(client_id = client_id))
        elif os.path.exists(basepath+path):
            self.send_response(200)
            mime = mimetypes.guess_type(path)[0]
            self.send_header("Content-type", mime)
            self.end_headers()
            
            self.wfile.write(open(basepath + path).read())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        
        client_id = self.path.strip("/")
        data = cgi.FieldStorage(fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
                     
        msg_type = data["type"].value
        if msg_type == "heartbeat":
            manager.heartbeat(client_id)
        else:
            if msg_type == "execute":
                resp = manager.execute(data["code"].value)
            elif msg_type == "complete":
                resp = manager.complete(data["code"].value, data["pos"].value)
            elif msg_type == "inspect":
                resp = manager.inspect(data['name'].value)
            elif msg_type == "connect":
                resp = manager.connect()
            elif msg_type == "history":
                resp = manager.history(data['index'].value)
            json.dump(resp, self.wfile)
    
    def do_PUT(self):
        '''Placeholder for future REP channel, need to figure out how it works'''
        pass

class IPyHttpServer(ThreadingMixIn, HTTPServer):
    pass

# IPython imports.
from IPython.utils.traitlets import Type
from IPython.zmq.kernelmanager import KernelManager, SubSocketChannel, \
    XReqSocketChannel, RepSocketChannel, HBSocketChannel

class HttpXReqSocketChannel(XReqSocketChannel):
    #---------------------------------------------------------------------------
    # 'XReqSocketChannel' interface
    #---------------------------------------------------------------------------
    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        if msg.msg_type == "execute_reply":
            manager.append(msg)
        else:
            manager.addreq(msg)
    """
        Useful for filtering namespace:
        filter( lambda x: not x.startswith('_') and x not in startns, 
                globals())
    """

class HttpSubSocketChannel(SubSocketChannel):
    #---------------------------------------------------------------------------
    # 'SubSocketChannel' interface
    #---------------------------------------------------------------------------
    
    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        manager.append(msg)

class HttpRepSocketChannel(RepSocketChannel):
    #---------------------------------------------------------------------------
    # 'RepSocketChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        pass

class HttpHBSocketChannel(HBSocketChannel):
    #---------------------------------------------------------------------------
    # 'HBSocketChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, since_last_heartbeat):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        pass


class HttpKernelManager(KernelManager):
    """ A KernelManager that provides signals and slots.
    """
    
    # Use Http-specific channel classes that emit signals.
    sub_channel_class = Type(HttpSubSocketChannel)
    xreq_channel_class = Type(HttpXReqSocketChannel)
    rep_channel_class = Type(HttpRepSocketChannel)
    hb_channel_class = Type(HttpHBSocketChannel)
    
    def __init__(self, *args, **kwargs):
        super(HttpKernelManager, self).__init__(*args, **kwargs)
        #Give kernel manager access to the CometManager
        manager.kernel_manager = self
