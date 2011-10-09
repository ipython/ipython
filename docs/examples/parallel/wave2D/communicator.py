#!/usr/bin/env python
"""A simple Communicator class that has N,E,S,W neighbors connected via 0MQ PEER sockets"""

import socket

import zmq

from IPython.parallel.util import disambiguate_url

class EngineCommunicator(object):
    """An object that connects Engines to each other.
    north and east sockets listen, while south and west sockets connect.
    
    This class is useful in cases where there is a set of nodes that
    must communicate only with their nearest neighbors.
    """
    
    def __init__(self, interface='tcp://*', identity=None):
        self._ctx = zmq.Context()
        self.north = self._ctx.socket(zmq.PAIR)
        self.west = self._ctx.socket(zmq.PAIR)
        self.south = self._ctx.socket(zmq.PAIR)
        self.east = self._ctx.socket(zmq.PAIR)
        
        # bind to ports
        northport = self.north.bind_to_random_port(interface)
        eastport = self.east.bind_to_random_port(interface)
        
        self.north_url = interface+":%i"%northport
        self.east_url = interface+":%i"%eastport
        
        # guess first public IP from socket
        self.location = socket.gethostbyname_ex(socket.gethostname())[-1][0]
    
    def __del__(self):
        self.north.close()
        self.south.close()
        self.east.close()
        self.west.close()
        self._ctx.term()
    
    @property
    def info(self):
        """return the connection info for this object's sockets."""
        return (self.location, self.north_url, self.east_url)
    
    def connect(self, south_peer=None, west_peer=None):
        """connect to peers.  `peers` will be a 3-tuples, of the form:
        (location, north_addr, east_addr)
        as produced by
        """
        if south_peer is not None:
            location, url, _ = south_peer
            self.south.connect(disambiguate_url(url, location))
        if west_peer is not None:
            location, _, url = west_peer
            self.west.connect(disambiguate_url(url, location))
    

