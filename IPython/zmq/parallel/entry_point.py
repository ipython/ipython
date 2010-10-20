""" Defines helper functions for creating kernel entry points and process
launchers.
"""

# Standard library imports.
import logging
import atexit
import os
import socket
from subprocess import Popen, PIPE
import sys

# System library imports.
import zmq
from zmq.log import handlers
# Local imports.
from IPython.core.ultratb import FormattedTB
from IPython.external.argparse import ArgumentParser
from IPython.zmq.log import logger

def split_ports(s, n):
    """Parser helper for multiport strings"""
    if not s:
        return tuple([0]*n)
    ports = map(int, s.split(','))
    if len(ports) != n:
        raise ValueError
    return ports

def select_random_ports(n):
    """Selects and return n random ports that are open."""
    ports = []
    for i in xrange(n):
        sock = socket.socket()
        sock.bind(('', 0))
        ports.append(sock)
    for i, sock in enumerate(ports):
        port = sock.getsockname()[1]
        sock.close()
        ports[i] = port
    return ports
        

def make_argument_parser():
    """ Creates an ArgumentParser for the generic arguments supported by all 
    ipcluster entry points.
    """
    parser = ArgumentParser()
    parser.add_argument('--ip', type=str, default='127.0.0.1',
                        help='set the controller\'s IP address [default: local]')
    parser.add_argument('--transport', type=str, default='tcp',
                        help='set the transport to use [default: tcp]')
    parser.add_argument('--regport', type=int, metavar='PORT', default=10101,
                        help='set the XREP port for registration [default: 10101]')
    parser.add_argument('--logport', type=int, metavar='PORT', default=20202,
                        help='set the PUB port for logging [default: 10201]')
    parser.add_argument('--loglevel', type=int, metavar='LEVEL', default=logging.DEBUG,
                        help='set the log level [default: DEBUG]')
    parser.add_argument('--ident', type=str,
                        help='set the ZMQ identity [default: random]')
    parser.add_argument('--url', type=str,
                        help='set transport,ip,regport in one arg, e.g. tcp://127.0.0.1:10101')

    return parser


def connect_logger(context, iface, root="ip", loglevel=logging.DEBUG):
    lsock = context.socket(zmq.PUB)
    lsock.connect(iface)
    handler = handlers.PUBHandler(lsock)
    handler.setLevel(loglevel)
    handler.root_topic = root
    logger.addHandler(handler)
    