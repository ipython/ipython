"""utilities for checking zmq versions"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Verify zmq version dependency >= 2.1.11
#-----------------------------------------------------------------------------

from IPython.utils.version import check_version


def patch_pyzmq():
    """backport a few patches from newer pyzmq
    
    These can be removed as we bump our minimum pyzmq version
    """
    
    import zmq
    
    # fallback on stdlib json if jsonlib is selected, because jsonlib breaks things.
    # jsonlib support is removed from pyzmq >= 2.2.0

    from zmq.utils import jsonapi
    if jsonapi.jsonmod.__name__ == 'jsonlib':
        import json
        jsonapi.jsonmod = json


def check_for_zmq(minimum_version, required_by='Someone'):
    try:
        import zmq
    except ImportError:
        raise ImportError("%s requires pyzmq >= %s"%(required_by, minimum_version))
    
    patch_pyzmq()
    
    pyzmq_version = zmq.__version__
    
    if not check_version(pyzmq_version, minimum_version):
        raise ImportError("%s requires pyzmq >= %s, but you have %s"%(
                        required_by, minimum_version, pyzmq_version))

