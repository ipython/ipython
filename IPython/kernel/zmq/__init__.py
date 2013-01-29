#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Verify zmq version dependency >= 2.1.11
#-----------------------------------------------------------------------------

import warnings
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


def check_for_zmq(minimum_version, module='IPython.kernel.zmq'):
    try:
        import zmq
    except ImportError:
        raise ImportError("%s requires pyzmq >= %s"%(module, minimum_version))

    pyzmq_version = zmq.__version__
    
    if not check_version(pyzmq_version, minimum_version):
        raise ImportError("%s requires pyzmq >= %s, but you have %s"%(
                        module, minimum_version, pyzmq_version))

check_for_zmq('2.1.11')
patch_pyzmq()

from .session import Session

