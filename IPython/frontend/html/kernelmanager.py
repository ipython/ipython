""" Defines a KernelManager that provides signals and slots.
"""
# IPython imports.
from IPython.utils.traitlets import Type
from IPython.zmq.kernelmanager import KernelManager, SubSocketChannel, \
    XReqSocketChannel, RepSocketChannel, HBSocketChannel

import time
import json
import Queue
import threading
from string import Template
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class CometManager(object):
    def __init__(self):
        self.clients = {}
        
    def register(self, client_id):
        self.clients[client_id] = Queue.Queue()
    
    def get(self, client_id):
        return self.clients[client_id].get()
    
    def append(self, msg):
        for q in self.clients.values():
            q.put(msg)
    
    def __contains__(self, item):
        return item in self.clients
            
manager = CometManager()

class IPyHttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_id = self.path.strip("/")
        if self.path == "/notebook":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            client_id = str(time.time())
            manager.register(client_id)
            page_text = Template(open("notebook.html").read())
            
            self.wfile.write(page_text.safe_substitute(client_id = client_id))
        elif client_id in manager:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            #Manager.get blocks until a message is available
            msg = json.dumps(manager.get(client_id))
            self.wfile.write(msg)
        else:
            self.send_response(404)
            self.end_headers()

class IPyHttpServer(ThreadingMixIn, HTTPServer):
    pass

class HttpXReqSocketChannel(XReqSocketChannel):
    # Used by the first_reply signal logic to determine if a reply is the 
    # first.
    _handlers_called = False

    #---------------------------------------------------------------------------
    # 'XReqSocketChannel' interface
    #---------------------------------------------------------------------------
    
    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        if not self._handlers_called:
            self._handlers_called = True

    #---------------------------------------------------------------------------
    # 'HttpXReqSocketChannel' interface
    #---------------------------------------------------------------------------

    def reset_first_reply(self):
        """ Reset the first_reply signal to fire again on the next reply.
        """
        self._handlers_called = False


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

