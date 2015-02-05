"""Utilities for checking zmq versions."""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.utils.version import check_version


def check_for_zmq(minimum_version, required_by='Someone'):
    try:
        import zmq
    except ImportError:
        raise ImportError("%s requires pyzmq >= %s"%(required_by, minimum_version))
    
    pyzmq_version = zmq.__version__
    
    if not check_version(pyzmq_version, minimum_version):
        raise ImportError("%s requires pyzmq >= %s, but you have %s"%(
                        required_by, minimum_version, pyzmq_version))

