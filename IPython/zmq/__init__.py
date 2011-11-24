#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Verify zmq version dependency >= 2.1.4
#-----------------------------------------------------------------------------

import re
import warnings

def check_for_zmq(minimum_version, module='IPython.zmq'):
    min_vlist = [int(n) for n in minimum_version.split('.')]

    try:
        import zmq
    except ImportError:
        raise ImportError("%s requires pyzmq >= %s"%(module, minimum_version))

    pyzmq_version = zmq.__version__
    vlist = [int(n) for n in re.findall(r'\d+', pyzmq_version)]

    if 'dev' not in pyzmq_version and vlist < min_vlist:
        raise ImportError("%s requires pyzmq >= %s, but you have %s"%(
                        module, minimum_version, pyzmq_version))

    # fix missing DEALER/ROUTER aliases in pyzmq < 2.1.9
    if not hasattr(zmq, 'DEALER'):
        zmq.DEALER = zmq.XREQ
    if not hasattr(zmq, 'ROUTER'):
        zmq.ROUTER = zmq.XREP

    if zmq.zmq_version() >= '4.0.0':
        warnings.warn("""libzmq 4 detected.
        It is unlikely that IPython's zmq code will work properly.
        Please install libzmq stable, which is 2.1.x or 2.2.x""",
        RuntimeWarning)

check_for_zmq('2.1.4')
