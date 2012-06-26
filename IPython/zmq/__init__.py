#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Verify zmq version dependency >= 2.1.4
#-----------------------------------------------------------------------------

import warnings
from distutils.version import LooseVersion as V


def patch_pyzmq():
    """backport a few patches from newer pyzmq
    
    These can be removed as we bump our minimum pyzmq version
    """
    
    import zmq
    
    # ioloop.install, introduced in pyzmq 2.1.7
    from zmq.eventloop import ioloop
    
    def install():
        import tornado.ioloop
        tornado.ioloop.IOLoop = ioloop.IOLoop
    
    if not hasattr(ioloop, 'install'):
        ioloop.install = install
    
    # fix missing DEALER/ROUTER aliases in pyzmq < 2.1.9
    if not hasattr(zmq, 'DEALER'):
        zmq.DEALER = zmq.XREQ
    if not hasattr(zmq, 'ROUTER'):
        zmq.ROUTER = zmq.XREP
    
    # fallback on stdlib json if jsonlib is selected, because jsonlib breaks things.
    # jsonlib support is removed from pyzmq >= 2.2.0

    from zmq.utils import jsonapi
    if jsonapi.jsonmod.__name__ == 'jsonlib':
        import json
        jsonapi.jsonmod = json


def check_for_zmq(minimum_version, module='IPython.zmq'):
    try:
        import zmq
    except ImportError:
        raise ImportError("%s requires pyzmq >= %s"%(module, minimum_version))

    pyzmq_version = zmq.__version__
    
    if 'dev' not in pyzmq_version and V(pyzmq_version) < V(minimum_version):
        raise ImportError("%s requires pyzmq >= %s, but you have %s"%(
                        module, minimum_version, pyzmq_version))

    if V(zmq.zmq_version()) >= V('4.0.0'):
        warnings.warn("""libzmq 4 detected.
        It is unlikely that IPython's zmq code will work properly.
        Please install libzmq stable, which is 2.1.x or 2.2.x""",
        RuntimeWarning)

check_for_zmq('2.1.4')
patch_pyzmq()

from .blockingkernelmanager import BlockingKernelManager
from .kernelmanager import *
from .session import Session

