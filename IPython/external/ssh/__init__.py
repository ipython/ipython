"""This is a copy of zmq.ssh"""

try:
    from zmq.ssh import *
except ImportError:
    from . import tunnel
    from .tunnel import *
