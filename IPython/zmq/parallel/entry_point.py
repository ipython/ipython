""" Defines helper functions for creating kernel entry points and process
launchers.

************
NOTE: Most of this module has been deprecated by moving to Configurables
************
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

# Standard library imports.
import atexit
import logging
import os
import stat
import socket
import sys
from signal import signal, SIGINT, SIGABRT, SIGTERM
from subprocess import Popen, PIPE
try:
    from signal import SIGKILL
except ImportError:
    SIGKILL=None

# System library imports.
import zmq
from zmq.log import handlers

# Local imports.
from IPython.core.ultratb import FormattedTB
from IPython.external.argparse import ArgumentParser
from IPython.zmq.log import EnginePUBHandler

_random_ports = set()

def select_random_ports(n):
    """Selects and return n random ports that are available."""
    ports = []
    for i in xrange(n):
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
        logging.critical("Got signal %i, terminating children..."%sig)
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

def local_logger(logname, loglevel=logging.DEBUG):
    loglevel = integer_loglevel(loglevel)
    logger = logging.getLogger(logname)
    if any([isinstance(h, logging.StreamHandler) for h in logger.handlers]):
        # don't add a second StreamHandler
        return
    handler = logging.StreamHandler()
    handler.setLevel(loglevel)
    logger.addHandler(handler)
    logger.setLevel(loglevel)
