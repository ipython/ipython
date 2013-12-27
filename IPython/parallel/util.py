"""Some generic utilities for dealing with classes, urls, and serialization.

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports.
import logging
import os
import re
import stat
import socket
import sys
from signal import signal, SIGINT, SIGABRT, SIGTERM
try:
    from signal import SIGKILL
except ImportError:
    SIGKILL=None
from types import FunctionType

try:
    import cPickle
    pickle = cPickle
except:
    cPickle = None
    import pickle

# System library imports
import zmq
from zmq.log import handlers

from IPython.external.decorator import decorator

# IPython imports
from IPython.config.application import Application
from IPython.utils.localinterfaces import localhost, is_public_ip, public_ips
from IPython.utils.py3compat import string_types, iteritems, itervalues
from IPython.kernel.zmq.log import EnginePUBHandler
from IPython.kernel.zmq.serialize import (
    unserialize_object, serialize_object, pack_apply_message, unpack_apply_message
)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class Namespace(dict):
    """Subclass of dict for attribute access to keys."""
    
    def __getattr__(self, key):
        """getattr aliased to getitem"""
        if key in self:
            return self[key]
        else:
            raise NameError(key)

    def __setattr__(self, key, value):
        """setattr aliased to setitem, with strict"""
        if hasattr(dict, key):
            raise KeyError("Cannot override dict keys %r"%key)
        self[key] = value
    

class ReverseDict(dict):
    """simple double-keyed subset of dict methods."""
    
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._reverse = dict()
        for key, value in iteritems(self):
            self._reverse[value] = key
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self._reverse[key]
    
    def __setitem__(self, key, value):
        if key in self._reverse:
            raise KeyError("Can't have key %r on both sides!"%key)
        dict.__setitem__(self, key, value)
        self._reverse[value] = key
    
    def pop(self, key):
        value = dict.pop(self, key)
        self._reverse.pop(value)
        return value
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

@decorator
def log_errors(f, self, *args, **kwargs):
    """decorator to log unhandled exceptions raised in a method.
    
    For use wrapping on_recv callbacks, so that exceptions
    do not cause the stream to be closed.
    """
    try:
        return f(self, *args, **kwargs)
    except Exception:
        self.log.error("Uncaught exception in %r" % f, exc_info=True)
    

def is_url(url):
    """boolean check for whether a string is a zmq url"""
    if '://' not in url:
        return False
    proto, addr = url.split('://', 1)
    if proto.lower() not in ['tcp','pgm','epgm','ipc','inproc']:
        return False
    return True

def validate_url(url):
    """validate a url for zeromq"""
    if not isinstance(url, string_types):
        raise TypeError("url must be a string, not %r"%type(url))
    url = url.lower()
    
    proto_addr = url.split('://')
    assert len(proto_addr) == 2, 'Invalid url: %r'%url
    proto, addr = proto_addr
    assert proto in ['tcp','pgm','epgm','ipc','inproc'], "Invalid protocol: %r"%proto
    
    # domain pattern adapted from http://www.regexlib.com/REDetails.aspx?regexp_id=391
    # author: Remi Sabourin
    pat = re.compile(r'^([\w\d]([\w\d\-]{0,61}[\w\d])?\.)*[\w\d]([\w\d\-]{0,61}[\w\d])?$')
    
    if proto == 'tcp':
        lis = addr.split(':')
        assert len(lis) == 2, 'Invalid url: %r'%url
        addr,s_port = lis
        try:
            port = int(s_port)
        except ValueError:
            raise AssertionError("Invalid port %r in url: %r"%(port, url))
        
        assert addr == '*' or pat.match(addr) is not None, 'Invalid url: %r'%url
        
    else:
        # only validate tcp urls currently
        pass
    
    return True


def validate_url_container(container):
    """validate a potentially nested collection of urls."""
    if isinstance(container, string_types):
        url = container
        return validate_url(url)
    elif isinstance(container, dict):
        container = itervalues(container)
    
    for element in container:
        validate_url_container(element)


def split_url(url):
    """split a zmq url (tcp://ip:port) into ('tcp','ip','port')."""
    proto_addr = url.split('://')
    assert len(proto_addr) == 2, 'Invalid url: %r'%url
    proto, addr = proto_addr
    lis = addr.split(':')
    assert len(lis) == 2, 'Invalid url: %r'%url
    addr,s_port = lis
    return proto,addr,s_port
    
def disambiguate_ip_address(ip, location=None):
    """turn multi-ip interfaces '0.0.0.0' and '*' into connectable
    ones, based on the location (default interpretation of location is localhost)."""
    if ip in ('0.0.0.0', '*'):
        if location is None or is_public_ip(location) or not public_ips():
            # If location is unspecified or cannot be determined, assume local
            ip = localhost()
        elif location:
            return location
    return ip

def disambiguate_url(url, location=None):
    """turn multi-ip interfaces '0.0.0.0' and '*' into connectable
    ones, based on the location (default interpretation is localhost).
    
    This is for zeromq urls, such as ``tcp://*:10101``.
    """
    try:
        proto,ip,port = split_url(url)
    except AssertionError:
        # probably not tcp url; could be ipc, etc.
        return url
    
    ip = disambiguate_ip_address(ip,location)
    
    return "%s://%s:%s"%(proto,ip,port)


#--------------------------------------------------------------------------
# helpers for implementing old MEC API via view.apply
#--------------------------------------------------------------------------

def interactive(f):
    """decorator for making functions appear as interactively defined.
    This results in the function being linked to the user_ns as globals()
    instead of the module globals().
    """
    
    # build new FunctionType, so it can have the right globals
    # interactive functions never have closures, that's kind of the point
    if isinstance(f, FunctionType):
        mainmod = __import__('__main__')
        f = FunctionType(f.__code__, mainmod.__dict__,
            f.__name__, f.__defaults__,
        )
    # associate with __main__ for uncanning
    f.__module__ = '__main__'
    return f

@interactive
def _push(**ns):
    """helper method for implementing `client.push` via `client.apply`"""
    user_ns = globals()
    tmp = '_IP_PUSH_TMP_'
    while tmp in user_ns:
        tmp = tmp + '_'
    try:
        for name, value in ns.items():
            user_ns[tmp] = value
            exec("%s = %s" % (name, tmp), user_ns)
    finally:
        user_ns.pop(tmp, None)

@interactive
def _pull(keys):
    """helper method for implementing `client.pull` via `client.apply`"""
    if isinstance(keys, (list,tuple, set)):
        return [eval(key, globals()) for key in keys]
    else:
        return eval(keys, globals())

@interactive
def _execute(code):
    """helper method for implementing `client.execute` via `client.apply`"""
    exec(code, globals())

#--------------------------------------------------------------------------
# extra process management utilities
#--------------------------------------------------------------------------

_random_ports = set()

def select_random_ports(n):
    """Selects and return n random ports that are available."""
    ports = []
    for i in range(n):
        sock = socket.socket()
        sock.bind(('', 0))
        while sock.getsockname()[1] in _random_ports:
            sock.close()
            sock = socket.socket()
            sock.bind(('', 0))
        ports.append(sock)
    for i, sock in enumerate(ports):
        port = sock.getsockname()[1]
        sock.close()
        ports[i] = port
        _random_ports.add(port)
    return ports

def signal_children(children):
    """Relay interupt/term signals to children, for more solid process cleanup."""
    def terminate_children(sig, frame):
        log = Application.instance().log
        log.critical("Got signal %i, terminating children..."%sig)
        for child in children:
            child.terminate()
        
        sys.exit(sig != SIGINT)
        # sys.exit(sig)
    for sig in (SIGINT, SIGABRT, SIGTERM):
        signal(sig, terminate_children)

def generate_exec_key(keyfile):
    import uuid
    newkey = str(uuid.uuid4())
    with open(keyfile, 'w') as f:
        # f.write('ipython-key ')
        f.write(newkey+'\n')
    # set user-only RW permissions (0600)
    # this will have no effect on Windows
    os.chmod(keyfile, stat.S_IRUSR|stat.S_IWUSR)


def integer_loglevel(loglevel):
    try:
        loglevel = int(loglevel)
    except ValueError:
        if isinstance(loglevel, str):
            loglevel = getattr(logging, loglevel)
    return loglevel

def connect_logger(logname, context, iface, root="ip", loglevel=logging.DEBUG):
    logger = logging.getLogger(logname)
    if any([isinstance(h, handlers.PUBHandler) for h in logger.handlers]):
        # don't add a second PUBHandler
        return
    loglevel = integer_loglevel(loglevel)
    lsock = context.socket(zmq.PUB)
    lsock.connect(iface)
    handler = handlers.PUBHandler(lsock)
    handler.setLevel(loglevel)
    handler.root_topic = root
    logger.addHandler(handler)
    logger.setLevel(loglevel)

def connect_engine_logger(context, iface, engine, loglevel=logging.DEBUG):
    logger = logging.getLogger()
    if any([isinstance(h, handlers.PUBHandler) for h in logger.handlers]):
        # don't add a second PUBHandler
        return
    loglevel = integer_loglevel(loglevel)
    lsock = context.socket(zmq.PUB)
    lsock.connect(iface)
    handler = EnginePUBHandler(engine, lsock)
    handler.setLevel(loglevel)
    logger.addHandler(handler)
    logger.setLevel(loglevel)
    return logger

def local_logger(logname, loglevel=logging.DEBUG):
    loglevel = integer_loglevel(loglevel)
    logger = logging.getLogger(logname)
    if any([isinstance(h, logging.StreamHandler) for h in logger.handlers]):
        # don't add a second StreamHandler
        return
    handler = logging.StreamHandler()
    handler.setLevel(loglevel)
    formatter = logging.Formatter("%(asctime)s.%(msecs).03d [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(loglevel)
    return logger

def set_hwm(sock, hwm=0):
    """set zmq High Water Mark on a socket
    
    in a way that always works for various pyzmq / libzmq versions.
    """
    import zmq
    
    for key in ('HWM', 'SNDHWM', 'RCVHWM'):
        opt = getattr(zmq, key, None)
        if opt is None:
            continue
        try:
            sock.setsockopt(opt, hwm)
        except zmq.ZMQError:
            pass

        