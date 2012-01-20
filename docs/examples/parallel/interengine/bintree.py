"""
BinaryTree inter-engine communication class

use from bintree_script.py

Provides parallel [all]reduce functionality

"""

import cPickle as pickle
import re
import socket
import uuid

import zmq

from IPython.parallel.util import disambiguate_url


#----------------------------------------------------------------------------
# bintree-related construction/printing helpers
#----------------------------------------------------------------------------

def bintree(ids, parent=None):
    """construct {child:parent} dict representation of a binary tree
    
    keys are the nodes in the tree, and values are the parent of each node.
    
    The root node has parent `parent`, default: None.
    
    >>> tree = bintree(range(7))
    >>> tree
    {0: None, 1: 0, 2: 1, 3: 1, 4: 0, 5: 4, 6: 4}
    >>> print_bintree(tree)
    0
      1
        2
        3
      4
        5
        6
    """
    parents = {}
    n = len(ids)
    if n == 0:
        return parents
    root = ids[0]
    parents[root] = parent
    if len(ids) == 1:
        return parents
    else:
        ids = ids[1:]
        n = len(ids)
        left = bintree(ids[:n/2], parent=root)
        right = bintree(ids[n/2:], parent=root)
        parents.update(left)
        parents.update(right)
    return parents

def reverse_bintree(parents):
    """construct {parent:[children]} dict from {child:parent}
    
    keys are the nodes in the tree, and values are the lists of children
    of that node in the tree.
    
    reverse_tree[None] is the root node
    
    >>> tree = bintree(range(7))
    >>> reverse_bintree(tree)
    {None: 0, 0: [1, 4], 4: [5, 6], 1: [2, 3]}
    """
    children = {}
    for child,parent in parents.iteritems():
        if parent is None:
            children[None] = child
            continue
        elif parent not in children:
            children[parent] = []
        children[parent].append(child)
    
    return children

def depth(n, tree):
    """get depth of an element in the tree"""
    d = 0
    parent = tree[n]
    while parent is not None:
        d += 1
        parent = tree[parent]
    return d

def print_bintree(tree, indent='  '):
    """print a binary tree"""
    for n in sorted(tree.keys()):
        print "%s%s" % (indent * depth(n,tree), n)

#----------------------------------------------------------------------------
# Communicator class for a binary-tree map
#----------------------------------------------------------------------------

ip_pat = re.compile(r'^\d+\.\d+\.\d+\.\d+$')

def disambiguate_dns_url(url, location):
    """accept either IP address or dns name, and return IP"""
    if not ip_pat.match(location):
        location = socket.gethostbyname(location)
    return disambiguate_url(url, location)

class BinaryTreeCommunicator(object):
    
    id          = None
    pub         = None
    sub         = None
    downstream  = None
    upstream    = None
    pub_url     = None
    tree_url    = None
    
    def __init__(self, id, interface='tcp://*', root=False):
        self.id = id
        self.root = root
        
        # create context and sockets
        self._ctx = zmq.Context()
        if root:
            self.pub = self._ctx.socket(zmq.PUB)
        else:
            self.sub = self._ctx.socket(zmq.SUB)
            self.sub.setsockopt(zmq.SUBSCRIBE, b'')
        self.downstream = self._ctx.socket(zmq.PULL)
        self.upstream = self._ctx.socket(zmq.PUSH)
        
        # bind to ports
        interface_f = interface + ":%i"
        if self.root:
            pub_port = self.pub.bind_to_random_port(interface)
            self.pub_url = interface_f % pub_port
        
        tree_port = self.downstream.bind_to_random_port(interface)
        self.tree_url = interface_f % tree_port
        self.downstream_poller = zmq.Poller()
        self.downstream_poller.register(self.downstream, zmq.POLLIN)
        
        # guess first public IP from socket
        self.location = socket.gethostbyname_ex(socket.gethostname())[-1][0]
    
    def __del__(self):
        self.downstream.close()
        self.upstream.close()
        if self.root:
            self.pub.close()
        else:
            self.sub.close()
        self._ctx.term()
    
    @property
    def info(self):
        """return the connection info for this object's sockets."""
        return (self.tree_url, self.location)
    
    def connect(self, peers, btree, pub_url, root_id=0):
        """connect to peers.  `peers` will be a dict of 4-tuples, keyed by name.
        {peer : (ident, addr, pub_addr, location)}
        where peer is the name, ident is the XREP identity, addr,pub_addr are the
        """
        
        # count the number of children we have
        self.nchildren = btree.values().count(self.id)
        
        if self.root:
            return # root only binds
        
        root_location = peers[root_id][-1]
        self.sub.connect(disambiguate_dns_url(pub_url, root_location))
        
        parent = btree[self.id]
        
        tree_url, location = peers[parent]
        self.upstream.connect(disambiguate_dns_url(tree_url, location))
    
    def serialize(self, obj):
        """serialize objects.
        
        Must return list of sendable buffers.
        
        Can be extended for more efficient/noncopying serialization of numpy arrays, etc.
        """
        return [pickle.dumps(obj)]
    
    def unserialize(self, msg):
        """inverse of serialize"""
        return pickle.loads(msg[0])
    
    def publish(self, value):
        assert self.root
        self.pub.send_multipart(self.serialize(value))
    
    def consume(self):
        assert not self.root
        return self.unserialize(self.sub.recv_multipart())

    def send_upstream(self, value, flags=0):
        assert not self.root
        self.upstream.send_multipart(self.serialize(value), flags=flags|zmq.NOBLOCK)
    
    def recv_downstream(self, flags=0, timeout=2000.):
        # wait for a message, so we won't block if there was a bug
        self.downstream_poller.poll(timeout)
        
        msg = self.downstream.recv_multipart(zmq.NOBLOCK|flags)
        return self.unserialize(msg)
    
    def reduce(self, f, value, flat=True, all=False):
        """parallel reduce on binary tree
        
        if flat:
            value is an entry in the sequence
        else:
            value is a list of entries in the sequence
        
        if all:
            broadcast final result to all nodes
        else:
            only root gets final result
        """
        if not flat:
            value = reduce(f, value)
        
        for i in range(self.nchildren):
            value = f(value, self.recv_downstream())
        
        if not self.root:
            self.send_upstream(value)
        
        if all:
            if self.root:
                self.publish(value)
            else:
                value = self.consume()
        return value
    
    def allreduce(self, f, value, flat=True):
        """parallel reduce followed by broadcast of the result"""
        return self.reduce(f, value, flat=flat, all=True)

