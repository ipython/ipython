import socket

import uuid
import zmq

from IPython.parallel.util import disambiguate_url

class EngineCommunicator(object):
    
    def __init__(self, interface='tcp://*', identity=None):
        self._ctx = zmq.Context()
        self.socket = self._ctx.socket(zmq.XREP)
        self.pub = self._ctx.socket(zmq.PUB)
        self.sub = self._ctx.socket(zmq.SUB)
        
        # configure sockets
        self.identity = identity or bytes(uuid.uuid4())
        print self.identity
        self.socket.setsockopt(zmq.IDENTITY, self.identity)
        self.sub.setsockopt(zmq.SUBSCRIBE, b'')
        
        # bind to ports
        port = self.socket.bind_to_random_port(interface)
        pub_port = self.pub.bind_to_random_port(interface)
        self.url = interface+":%i"%port
        self.pub_url = interface+":%i"%pub_port
        # guess first public IP from socket
        self.location = socket.gethostbyname_ex(socket.gethostname())[-1][0]
        self.peers = {}
    
    def __del__(self):
        self.socket.close()
        self.pub.close()
        self.sub.close()
        self._ctx.term()
    
    @property
    def info(self):
        """return the connection info for this object's sockets."""
        return (self.identity, self.url, self.pub_url, self.location)
    
    def connect(self, peers):
        """connect to peers.  `peers` will be a dict of 4-tuples, keyed by name.
        {peer : (ident, addr, pub_addr, location)}
        where peer is the name, ident is the XREP identity, addr,pub_addr are the
        """
        for peer, (ident, url, pub_url, location) in peers.items():
            self.peers[peer] = ident
            if ident != self.identity:
                self.sub.connect(disambiguate_url(pub_url, location))
            if ident > self.identity:
                # prevent duplicate xrep, by only connecting
                # engines to engines with higher IDENTITY
                # a doubly-connected pair will crash
                self.socket.connect(disambiguate_url(url, location))
    
    def send(self, peers, msg, flags=0, copy=True):
        if not isinstance(peers, list):
            peers = [peers]
        if not isinstance(msg, list):
            msg = [msg]
        for p in peers:
            ident = self.peers[p]
            self.socket.send_multipart([ident]+msg, flags=flags, copy=copy)
        
    def recv(self, flags=0, copy=True):
        return self.socket.recv_multipart(flags=flags, copy=copy)[1:]
    
    def publish(self, msg, flags=0, copy=True):
        if not isinstance(msg, list):
            msg = [msg]
        self.pub.send_multipart(msg, copy=copy)

    def consume(self, flags=0, copy=True):
        return self.sub.recv_multipart(flags=flags, copy=copy)
    

